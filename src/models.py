"""Data models for Prisma SASE 5G resources."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time


@dataclass
class TenantUEMapping:
    """Represents a SIM Card / User Equipment (UE) mapping to a Tenant Service Group."""
    imsi: str
    imei: str
    apn: str
    tsg_id: Optional[str] = None
    root_tsg_id: Optional[str] = None
    identity_id: Optional[str] = None
    groups: List[Dict[str, Any]] = field(default_factory=list)
    tenant_name: Optional[str] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None

    def to_request_payload(self) -> Dict[str, Any]:
        """Convert to API JSON payload for POST /mt/manage/5g/tenantUEInfo."""
        payload = {
            "imsi": str(self.imsi),
            "imei": str(self.imei),
            "apn": str(self.apn),
        }
        if self.tsg_id:
            payload["tsg_id"] = str(self.tsg_id)
        if self.root_tsg_id:
            payload["root_tsg_id"] = str(self.root_tsg_id)
        return payload

    @classmethod
    def from_api_dict(cls, data: Dict[str, Any]) -> "TenantUEMapping":
        """Create an instance from an API JSON response object."""
        return cls(
            imsi=str(data.get("imsi", "")),
            imei=str(data.get("imei", "")),
            apn=str(data.get("apn", "")),
            tsg_id=data.get("tsg_id"),
            root_tsg_id=data.get("root_tsg_id"),
            identity_id=data.get("identity_id") or data.get("id"),
            groups=data.get("group", []),
            create_time=data.get("create_time"),
            update_time=data.get("update_time"),
        )


@dataclass
class UESession:
    """Represents real-time 5G subscriber session telemetry for registration/deregistration."""
    imsi: str
    imei: str
    apn: str
    ip_type: str = "IPv4"  # IPv4, IPv6, IPv4v6
    ipv4_addr: Optional[str] = None
    ipv6_addr: Optional[str] = None
    event_time: int = field(default_factory=lambda: int(time.time() * 1000))
    expiry_time: Optional[int] = None
    slice_id: Optional[str] = None
    msisdn: Optional[str] = None
    rat_type: Optional[str] = None
    cell_id: Optional[str] = None
    supi: Optional[str] = None

    def to_request_payload(self) -> Dict[str, Any]:
        """Convert to API item for POST /mt/manage/5g/register/ue or /mt/manage/5g/deregister/ue."""
        payload: Dict[str, Any] = {
            "imsi": str(self.imsi),
            "imei": str(self.imei),
            "apn": str(self.apn),
            "ipType": str(self.ip_type),
            "eventTime": int(self.event_time),
        }
        if self.ipv4_addr:
            payload["ipv4Addr"] = self.ipv4_addr
        if self.ipv6_addr:
            payload["ipv6Addr"] = self.ipv6_addr
        if self.expiry_time is not None:
            payload["expiryTime"] = int(self.expiry_time)
        if self.slice_id:
            payload["sliceId"] = self.slice_id
        if self.msisdn:
            payload["msisdn"] = self.msisdn
        if self.rat_type:
            payload["ratType"] = self.rat_type
        if self.cell_id:
            payload["cellId"] = self.cell_id
        if self.supi:
            payload["supi"] = self.supi
        return payload


@dataclass
class UserGroup:
    """Represents a named 5G subscriber group."""
    group_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    tsg_id: Optional[str] = None
    user_count: Optional[int] = None
    tenant_name: Optional[str] = None
    identity_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_api_dict(cls, data: Dict[str, Any]) -> "UserGroup":
        identities = data.get("identity_id") or data.get("identityIds") or []
        count = data.get("user_count")
        if count is None and isinstance(identities, list):
            count = len(identities)
        return cls(
            group_id=data.get("id") or data.get("group_id"),
            name=data.get("name") or data.get("group_name"),
            description=data.get("description"),
            tsg_id=data.get("tsg_id"),
            user_count=count,
            identity_ids=identities if isinstance(identities, list) else [],
        )
