"""Prisma Access 5G SASE API Client."""

import logging
from typing import List, Dict, Any, Optional, Union
import requests

from .config import Config, load_config
from .auth import PANWAuthManager
from .models import TenantUEMapping, UESession, UserGroup

logger = logging.getLogger("Prisma5GClient")


class Prisma5GClient:
    """Client for interacting with Palo Alto Networks Prisma Access 5G SASE APIs.
    
    Provides methods for:
    - Tenant UE Info (SIM card / hardware mapping CRUD)
    - Real-time UE Session Enrichment (Registration & Deregistration)
    - 5G Subscriber User Groups
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or load_config()
        self.auth = PANWAuthManager(self.config)
        self.base_url = self.config.api_base_url.rstrip("/")
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        retry_on_401: bool = True,
    ) -> requests.Response:
        """Internal helper to execute authenticated requests with automatic token refresh on 401."""
        url = f"{self.base_url}{path}"
        headers = self.auth.get_auth_headers()

        logger.debug("%s %s (params=%s, body=%s)", method, url, params, json_data)
        
        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers,
            timeout=30,
        )

        # If token expired or unauthorized, attempt 1 refresh
        if response.status_code == 401 and retry_on_401 and not self.config.auth_token:
            logger.info("Received 401 Unauthorized. Refreshing token and retrying...")
            headers = self.auth.get_auth_headers(force_refresh=True)
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=30,
            )

        return response

    # --------------------------------------------------------------------------
    # 0. Multitenant & Hierarchy Discovery
    # --------------------------------------------------------------------------

    def list_tenants(self, tsg_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all Tenant Service Groups (Root & Child Tenants).
        
        API: GET /tenancy/v1/tenant_service_groups or POST /tenancy/v1/tenant_service_groups/{id}/operations/list_children
        """
        root_tsg = tsg_id or self.config.tsg_id
        # First try listing all TSGs
        resp = self._request("GET", "/tenancy/v1/tenant_service_groups")
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", []) if isinstance(data, dict) else []
            return items

        # Fallback to list_children
        if root_tsg:
            resp_children = self._request(
                "POST",
                f"/tenancy/v1/tenant_service_groups/{root_tsg}/operations/list_children",
                json_data={},
            )
            if resp_children.status_code == 200:
                data = resp_children.json()
                return data.get("items", [])

        return []

    # --------------------------------------------------------------------------
    # 1. Tenant UE Info Management (Hardware SIM Mapping)
    # --------------------------------------------------------------------------

    def list_tenant_ues(
        self,
        tsg_id: Optional[str] = None,
        page: int = 0,
        size: int = 50,
        filter_query: Optional[str] = None,
        order_query: Optional[str] = None,
        all_tenants: bool = True,
    ) -> Dict[str, Any]:
        """List and search Tenant UE / SIM mappings across one or all child tenants.
        
        API: POST /mt/manage/5g/tenantUEInfo/list
        """
        configured_tsg = str(self.config.tsg_id) if self.config.tsg_id else None
        target_tsg = str(tsg_id) if tsg_id else configured_tsg

        if not target_tsg:
            raise ValueError("tsg_id must be provided or configured in .env (PANW_TSG_ID)")

        # Helper to query a single TSG
        def _query_single_tsg(tid: str, tenant_name: Optional[str] = None) -> List[Dict[str, Any]]:
            params: Dict[str, Any] = {"page": page, "size": size}
            if filter_query:
                params["filter"] = filter_query
            if order_query:
                params["order"] = order_query

            payload = {"tsg_id": str(tid)}
            resp = self._request("POST", "/mt/manage/5g/tenantUEInfo/list", params=params, json_data=payload)

            if resp.status_code == 204 or not resp.text or not resp.text.strip():
                return []
            if resp.status_code not in (200, 201):
                return []

            try:
                res_data = resp.json().get("data", [])
                for item in res_data:
                    if tenant_name:
                        item["tenant_name"] = tenant_name
                return res_data
            except Exception:
                return []

        # If explicit tsg_id passed, query only that TSG
        if tsg_id:
            items = _query_single_tsg(tsg_id)
            models = [TenantUEMapping.from_api_dict(item) for item in items]
            return {"totalItems": len(items), "data": items, "models": models}

        # Otherwise, check if configured TSG has child tenants
        tenants = self.list_tenants(target_tsg)
        tenant_map = {str(t.get("id")): t.get("display_name") for t in tenants}

        all_items: List[Dict[str, Any]] = []

        # Query child tenants (and root)
        if tenants:
            for t in tenants:
                tid = str(t.get("id"))
                tname = t.get("display_name", tid)
                t_items = _query_single_tsg(tid, tenant_name=tname)
                all_items.extend(t_items)
        else:
            all_items = _query_single_tsg(target_tsg)

        models = []
        for item in all_items:
            m = TenantUEMapping.from_api_dict(item)
            m.tenant_name = tenant_map.get(str(m.tsg_id))
            models.append(m)

        return {
            "totalItems": len(all_items),
            "data": all_items,
            "models": models,
        }

    def get_tenant_ue(self, ue_info_id: str, unknown_ues: bool = False) -> Dict[str, Any]:
        """Fetch a specific Tenant-UE mapping by ID.
        
        API: GET /mt/manage/5g/tenantUEInfo/{ueInfoId}
        """
        params = {"unknownUes": unknown_ues} if unknown_ues else None
        resp = self._request("GET", f"/mt/manage/5g/tenantUEInfo/{ue_info_id}", params=params)

        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch Tenant UE '{ue_info_id}' [HTTP {resp.status_code}]: {resp.text}"
            )

        return resp.json()

    def create_tenant_ue(
        self,
        imsi: str,
        imei: str,
        apn: Optional[str] = None,
        tsg_id: Optional[str] = None,
        root_tsg_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add / register a new SIM card mapping to a Tenant.
        
        API: POST /mt/manage/5g/tenantUEInfo
        """
        configured_tsg = self.config.tsg_id
        target_tsg = tsg_id or configured_tsg
        target_apn = apn or self.config.default_apn
        target_root_tsg = root_tsg_id

        if not target_tsg:
            raise ValueError("tsg_id must be provided or configured in .env (PANW_TSG_ID)")

        # Auto-detect root_tsg_id if not provided
        if not target_root_tsg:
            tenants = self.list_tenants(configured_tsg)
            # Check if target_tsg is a child
            for t in tenants:
                if str(t.get("id")) == str(target_tsg):
                    target_root_tsg = t.get("parent_id") or configured_tsg
                    break
            if not target_root_tsg:
                target_root_tsg = configured_tsg

        mapping = TenantUEMapping(
            imsi=imsi,
            imei=imei,
            apn=target_apn,
            tsg_id=target_tsg,
            root_tsg_id=target_root_tsg,
        )

        payload = mapping.to_request_payload()
        resp = self._request("POST", "/mt/manage/5g/tenantUEInfo", json_data=payload)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to create Tenant UE [HTTP {resp.status_code}]: {resp.text}"
            )

        data = resp.json()
        if "data" in data and isinstance(data["data"], dict):
            data["model"] = TenantUEMapping.from_api_dict(data["data"])
        return data

    def update_tenant_ue(
        self,
        identity_id: str,
        imsi: Optional[str] = None,
        imei: Optional[str] = None,
        apn: Optional[str] = None,
        tsg_id: Optional[str] = None,
        root_tsg_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing Tenant-UE mapping.
        
        API: PUT /mt/manage/5g/tenantUEInfo/{identity_id}
        """
        payload: Dict[str, Any] = {}
        if tsg_id or self.config.tsg_id:
            payload["tsg_id"] = str(tsg_id or self.config.tsg_id)
        if imsi:
            payload["imsi"] = str(imsi)
        if imei:
            payload["imei"] = str(imei)
        if apn:
            payload["apn"] = str(apn)
        if root_tsg_id:
            payload["root_tsg_id"] = str(root_tsg_id)

        resp = self._request("PUT", f"/mt/manage/5g/tenantUEInfo/{identity_id}", json_data=payload)

        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to update Tenant UE '{identity_id}' [HTTP {resp.status_code}]: {resp.text}"
            )

        return resp.json()

    def delete_tenant_ue(self, identity_id: str) -> Dict[str, Any]:
        """Delete a single Tenant-UE mapping record.
        
        API: DELETE /mt/manage/5g/tenantUEInfo/{identity_id}
        """
        resp = self._request("DELETE", f"/mt/manage/5g/tenantUEInfo/{identity_id}")

        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"Failed to delete Tenant UE '{identity_id}' [HTTP {resp.status_code}]: {resp.text}"
            )

        try:
            return resp.json()
        except Exception:
            return {"status": "success", "identity_id": identity_id}

    def bulk_delete_tenant_ues(self, identity_ids: List[str]) -> Dict[str, Any]:
        """Remove multiple Tenant-UE mappings simultaneously.
        
        API: POST /mt/manage/5g/tenantUEInfo/delete
        """
        payload = {"identityIds": identity_ids}
        resp = self._request("POST", "/mt/manage/5g/tenantUEInfo/delete", json_data=payload)

        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"Failed to bulk delete Tenant UEs [HTTP {resp.status_code}]: {resp.text}"
            )

        try:
            return resp.json()
        except Exception:
            return {"status": "success", "deleted_count": len(identity_ids)}

    # --------------------------------------------------------------------------
    # 2. UE Session Enrichment (Real-time Subscriber Sessions)
    # --------------------------------------------------------------------------

    def register_ue_session(
        self,
        sessions: Union[UESession, List[UESession], Dict[str, Any], List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Initiate real-time subscriber session registration for one or more UEs.
        
        API: POST /mt/manage/5g/register/ue
        """
        if isinstance(sessions, (UESession, dict)):
            items = [sessions]
        else:
            items = list(sessions)

        payload = [
            item.to_request_payload() if isinstance(item, UESession) else item
            for item in items
        ]

        resp = self._request("POST", "/mt/manage/5g/register/ue", json_data=payload)

        if resp.status_code not in (200, 202, 207):
            raise RuntimeError(
                f"Failed to register UE subscriber session [HTTP {resp.status_code}]: {resp.text}"
            )

        try:
            return {"status_code": resp.status_code, "response": resp.json()}
        except Exception:
            return {"status_code": resp.status_code, "status": "Accepted"}

    def deregister_ue_session(
        self,
        sessions: Union[UESession, List[UESession], Dict[str, Any], List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Terminate real-time subscriber session for one or more UEs.
        
        API: POST /mt/manage/5g/deregister/ue
        """
        if isinstance(sessions, (UESession, dict)):
            items = [sessions]
        else:
            items = list(sessions)

        payload = [
            item.to_request_payload() if isinstance(item, UESession) else item
            for item in items
        ]

        resp = self._request("POST", "/mt/manage/5g/deregister/ue", json_data=payload)

        if resp.status_code not in (200, 202):
            raise RuntimeError(
                f"Failed to deregister UE subscriber session [HTTP {resp.status_code}]: {resp.text}"
            )

        try:
            return {"status_code": resp.status_code, "response": resp.json()}
        except Exception:
            return {"status_code": resp.status_code, "status": "Accepted"}

    # --------------------------------------------------------------------------
    # 3. 5G Subscriber User Groups
    # --------------------------------------------------------------------------

    def list_user_groups(
        self,
        tsg_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List subscriber user groups across one or all child tenants.
        
        API: POST /mt/manage/5g/userGroup/list
        """
        configured_tsg = str(self.config.tsg_id) if self.config.tsg_id else None
        target_tsg = str(tsg_id) if tsg_id else configured_tsg

        if not target_tsg:
            raise ValueError("tsg_id must be provided or configured in .env (PANW_TSG_ID)")

        def _query_group_for_tsg(tid: str, tenant_name: Optional[str] = None) -> List[UserGroup]:
            payload: Dict[str, Any] = {"tsg_id": str(tid)}
            if group_id:
                payload["group_id"] = str(group_id)

            resp = self._request("POST", "/mt/manage/5g/userGroup/list", json_data=payload)
            if resp.status_code == 204 or not resp.text or not resp.text.strip():
                return []
            if resp.status_code not in (200, 201):
                return []

            try:
                result = resp.json()
                items = result.get("data", []) if isinstance(result, dict) else (result if isinstance(result, list) else [])
                res_models = []
                for item in items:
                    m = UserGroup.from_api_dict(item)
                    if tenant_name:
                        m.tenant_name = tenant_name
                    res_models.append(m)
                return res_models
            except Exception:
                return []

        if tsg_id:
            models = _query_group_for_tsg(tsg_id)
            return {"models": models}

        tenants = self.list_tenants(target_tsg)
        all_models = []
        if tenants:
            for t in tenants:
                tid = str(t.get("id"))
                tname = t.get("display_name", tid)
                all_models.extend(_query_group_for_tsg(tid, tenant_name=tname))
        else:
            all_models = _query_group_for_tsg(target_tsg)

        return {"models": all_models}
