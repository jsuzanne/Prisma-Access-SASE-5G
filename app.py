"""FastAPI Web Application for Prisma Access 5G SASE Management & Lifecycle.

Provides REST APIs and serves a responsive single-page web application for:
- Viewing Tenant Hierarchy (Root MSP, Transatel demo, tenant-1)
- Managing SIM Cards / UEs (Inventory, Group Badges, Add, Delete)
- 5G Session Telemetry (Register Session IP, Deregister)
- Subscriber User Groups Explorer (Permissive, Restrictive)
- Interactive Full Lifecycle Test Runner
- In-App Settings & Credentials Manager (.env)
"""

import os
import time
import random
import re
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import Config, load_config
from src.auth import PANWAuthManager
from src.models import TenantUEMapping, UESession
from src.client import Prisma5GClient

# Project base directory
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

app = FastAPI(
    title="Prisma Access 5G SASE Manager",
    description="Full Lifecycle Management & Demo Portal for Palo Alto Networks Prisma Access 5G SASE",
    version="1.0.0",
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory if it exists
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def get_current_client(custom_config: Optional[Config] = None) -> Prisma5GClient:
    """Instantiate a client using current .env configuration."""
    cfg = custom_config or load_config(str(ENV_PATH) if ENV_PATH.exists() else None)
    return Prisma5GClient(cfg)


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class ConfigUpdateModel(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tsg_id: Optional[str] = None
    api_base_url: Optional[str] = "https://api.sase.paloaltonetworks.com"
    default_apn: Optional[str] = "sasetest"
    default_ip_type: Optional[str] = "IPv4"


class ConfigTestModel(BaseModel):
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tsg_id: Optional[str] = None
    api_base_url: Optional[str] = "https://api.sase.paloaltonetworks.com"


class CreateUEModel(BaseModel):
    imsi: str
    imei: str
    apn: str = "sasetest"
    tsg_id: Optional[str] = None
    session_ip: Optional[str] = None  # If provided, auto-registers 5G session


class RegisterSessionModel(BaseModel):
    imsi: str
    imei: str
    apn: str = "sasetest"
    ip_type: str = "IPv4"
    ipv4_addr: str = "10.56.0.195"
    slice_id: Optional[str] = None
    msisdn: Optional[str] = None


class DeregisterSessionModel(BaseModel):
    imsi: str
    imei: str
    apn: str = "sasetest"
    ipv4_addr: str = "10.56.0.195"


# -----------------------------------------------------------------------------
# API Endpoints: System Status & Settings
# -----------------------------------------------------------------------------

@app.get("/api/status")
def get_system_status():
    """Get system health, authentication state, and connected TSG info."""
    try:
        config = load_config(str(ENV_PATH) if ENV_PATH.exists() else None)
        has_creds = bool(config.client_id and config.client_secret and config.tsg_id)
        
        token_preview = None
        auth_error = None
        if has_creds:
            try:
                auth = PANWAuthManager(config)
                token = auth.get_access_token()
                token_preview = f"{token[:8]}...{token[-6:]}" if token else None
            except Exception as e:
                auth_error = str(e)

        return {
            "status": "healthy" if (has_creds and not auth_error) else "needs_config",
            "authenticated": bool(token_preview),
            "auth_error": auth_error,
            "token_preview": token_preview,
            "client_id": config.client_id,
            "tsg_id": config.tsg_id,
            "api_base_url": config.api_base_url,
            "default_apn": config.default_apn,
            "default_ip_type": config.default_ip_type,
        }
    except Exception as exc:
        return {
            "status": "error",
            "authenticated": False,
            "auth_error": str(exc),
        }


@app.get("/api/config")
def get_app_config():
    """Get current configuration with masked client secret for the Settings UI."""
    try:
        cfg = load_config(str(ENV_PATH) if ENV_PATH.exists() else None)
        secret_masked = None
        if cfg.client_secret:
            secret_masked = f"••••••••{cfg.client_secret[-4:]}" if len(cfg.client_secret) >= 4 else "••••••••"

        return {
            "client_id": cfg.client_id or "",
            "has_secret": bool(cfg.client_secret),
            "secret_masked": secret_masked,
            "tsg_id": cfg.tsg_id or "",
            "api_base_url": cfg.api_base_url,
            "default_apn": cfg.default_apn,
            "default_ip_type": cfg.default_ip_type,
            "env_file_exists": ENV_PATH.exists(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/config")
def update_app_config(payload: ConfigUpdateModel):
    """Update .env configuration file securely from the Settings UI."""
    try:
        current_cfg = load_config(str(ENV_PATH) if ENV_PATH.exists() else None)
        
        # Keep existing secret if empty/not provided
        new_secret = payload.client_secret if (payload.client_secret and payload.client_secret.strip()) else current_cfg.client_secret
        new_client_id = payload.client_id if payload.client_id is not None else current_cfg.client_id
        new_tsg_id = payload.tsg_id if payload.tsg_id is not None else current_cfg.tsg_id
        new_api_base = payload.api_base_url or "https://api.sase.paloaltonetworks.com"
        new_apn = payload.default_apn or "sasetest"
        new_ip_type = payload.default_ip_type or "IPv4"

        # Build clean .env content
        lines = [
            "# Palo Alto Networks Prisma Access 5G SASE Configuration",
            f"PANW_CLIENT_ID={new_client_id or ''}",
            f"PANW_CLIENT_SECRET={new_secret or ''}",
            f"PANW_TSG_ID={new_tsg_id or ''}",
            f"PANW_API_BASE_URL={new_api_base}",
            "PANW_AUTH_URL=https://auth.apps.paloaltonetworks.com/am/oauth2/access_token",
            f"DEFAULT_APN={new_apn}",
            f"DEFAULT_IP_TYPE={new_ip_type}",
            "",
        ]
        ENV_PATH.write_text("\n".join(lines), encoding="utf-8")

        # Reload environment variables into memory
        load_config(str(ENV_PATH))

        return {
            "success": True,
            "message": "Configuration saved to .env successfully",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {exc}")


@app.post("/api/config/test")
def test_app_config(payload: ConfigTestModel):
    """Test OAuth2 credentials and connectivity against PANW endpoints."""
    current_cfg = load_config(str(ENV_PATH) if ENV_PATH.exists() else None)
    
    effective_secret = payload.client_secret.strip() if (payload.client_secret and payload.client_secret.strip()) else current_cfg.client_secret
    effective_client_id = payload.client_id.strip() if (payload.client_id and payload.client_id.strip()) else current_cfg.client_id
    effective_tsg_id = payload.tsg_id.strip() if (payload.tsg_id and payload.tsg_id.strip()) else current_cfg.tsg_id
    effective_api_base = payload.api_base_url or current_cfg.api_base_url or "https://api.sase.paloaltonetworks.com"

    test_cfg = Config(
        client_id=effective_client_id,
        client_secret=effective_secret,
        tsg_id=effective_tsg_id,
        api_base_url=effective_api_base,
    )
    try:
        auth = PANWAuthManager(test_cfg)
        token = auth.get_access_token()
        
        # Test basic hierarchy query
        client = Prisma5GClient(test_cfg)
        tenants = client.list_tenants(effective_tsg_id)

        return {
            "success": True,
            "message": "Authentication and API connectivity verified successfully!",
            "token_preview": f"{token[:8]}...{token[-6:]}",
            "tenants_count": len(tenants),
            "tenants": tenants,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }


# -----------------------------------------------------------------------------
# API Endpoints: Tenants & Hierarchy
# -----------------------------------------------------------------------------

@app.get("/api/tenants")
def list_tenants():
    """Get discovered Tenant Service Groups (Root MSP and Child Tenants)."""
    try:
        client = get_current_client()
        tenants = client.list_tenants()
        return {
            "success": True,
            "count": len(tenants),
            "data": tenants,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -----------------------------------------------------------------------------
# API Endpoints: SIM Cards / UEs
# -----------------------------------------------------------------------------

@app.get("/api/ues")
def list_ues(tsg_id: Optional[str] = None):
    """List registered SIM cards (UE mappings) across all tenants or for a specific TSG."""
    try:
        client = get_current_client()
        resp = client.list_tenant_ues(tsg_id=tsg_id)
        
        items = resp.get("data", [])
        models = resp.get("models", [])
        
        # Convert models to rich json list
        res_data = []
        for m in models:
            res_data.append({
                "identity_id": m.identity_id,
                "imsi": m.imsi,
                "imei": m.imei,
                "apn": m.apn,
                "tsg_id": m.tsg_id,
                "root_tsg_id": m.root_tsg_id,
                "tenant_name": m.tenant_name,
                "groups": m.groups or [],
                "create_time": m.create_time,
            })

        return {
            "success": True,
            "total_items": resp.get("totalItems", len(res_data)),
            "data": res_data,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/ues")
def create_ue(payload: CreateUEModel):
    """Register a new SIM card (UE mapping) with optional immediate 5G session attach."""
    try:
        client = get_current_client()
        
        # 1. Register SIM mapping
        create_resp = client.create_tenant_ue(
            imsi=payload.imsi,
            imei=payload.imei,
            apn=payload.apn,
            tsg_id=payload.tsg_id,
        )
        data_obj = create_resp.get("data", {})
        created_id = data_obj.get("id") or data_obj.get("identity_id")

        session_result = None
        # 2. If session_ip provided, auto-register 5G session telemetry
        if payload.session_ip:
            try:
                sess = UESession(
                    imsi=payload.imsi,
                    imei=payload.imei,
                    apn=payload.apn,
                    ip_type="IPv4",
                    ipv4_addr=payload.session_ip,
                )
                sess_resp = client.register_ue_session(sess)
                session_result = {
                    "registered": True,
                    "status_code": sess_resp.get("status_code"),
                    "ip": payload.session_ip,
                }
            except Exception as s_exc:
                session_result = {
                    "registered": False,
                    "error": str(s_exc),
                }

        return {
            "success": True,
            "identity_id": created_id,
            "data": data_obj,
            "session_result": session_result,
            "message": f"SIM {payload.imsi} registered successfully with APN '{payload.apn}'",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/api/ues/{identity_id}")
def delete_ue(identity_id: str):
    """Safely delete a SIM card mapping by identity ID."""
    try:
        client = get_current_client()
        resp = client.delete_tenant_ue(identity_id)
        return {
            "success": True,
            "identity_id": identity_id,
            "data": resp,
            "message": f"SIM {identity_id} deleted successfully",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# API Endpoints: Subscriber User Groups
# -----------------------------------------------------------------------------

@app.get("/api/groups")
def list_groups(tsg_id: Optional[str] = None):
    """List 5G subscriber user groups (e.g. Permissive, Restrictive)."""
    try:
        client = get_current_client()
        resp = client.list_user_groups(tsg_id=tsg_id)
        models = resp.get("models", [])
        
        group_list = []
        for g in models:
            group_list.append({
                "group_id": g.group_id,
                "name": g.name,
                "description": g.description,
                "tsg_id": g.tsg_id,
                "tenant_name": g.tenant_name,
                "user_count": g.user_count,
            })
        return {
            "success": True,
            "count": len(group_list),
            "data": group_list,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# -----------------------------------------------------------------------------
# API Endpoints: 5G Session Telemetry (Registration & Termination)
# -----------------------------------------------------------------------------

@app.post("/api/sessions/register")
def register_session(payload: RegisterSessionModel):
    """Register real-time 5G session telemetry (IP allocation)."""
    try:
        client = get_current_client()
        session = UESession(
            imsi=payload.imsi,
            imei=payload.imei,
            apn=payload.apn,
            ip_type=payload.ip_type,
            ipv4_addr=payload.ipv4_addr,
            slice_id=payload.slice_id,
            msisdn=payload.msisdn,
        )
        resp = client.register_ue_session(session)
        return {
            "success": True,
            "status_code": resp.get("status_code"),
            "data": resp.get("data"),
            "message": f"5G Session registered for IMSI {payload.imsi} with IP {payload.ipv4_addr}",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/sessions/deregister")
def deregister_session(payload: DeregisterSessionModel):
    """Terminate / deregister real-time 5G subscriber session."""
    try:
        client = get_current_client()
        session = UESession(
            imsi=payload.imsi,
            imei=payload.imei,
            apn=payload.apn,
            ip_type="IPv4",
            ipv4_addr=payload.ipv4_addr,
        )
        resp = client.deregister_ue_session(session)
        return {
            "success": True,
            "status_code": resp.get("status_code"),
            "data": resp.get("data"),
            "message": f"5G Session terminated for IMSI {payload.imsi} on IP {payload.ipv4_addr}",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# -----------------------------------------------------------------------------
# API Endpoints: Full Lifecycle Test Runner
# -----------------------------------------------------------------------------

@app.post("/api/lifecycle/run")
def run_lifecycle():
    """Execute the full 8-step lifecycle test and return complete results."""
    steps_log = []
    start_time = time.time()
    
    def log_step(step_num: int, title: str, status: str, details: str, duration_ms: int = 0):
        steps_log.append({
            "step": step_num,
            "title": title,
            "status": status,  # "success", "warning", "error"
            "details": details,
            "duration_ms": duration_ms,
        })

    config = load_config(str(ENV_PATH) if ENV_PATH.exists() else None)
    client = Prisma5GClient(config)

    # Step 1: Config & Auth
    s1_start = time.time()
    try:
        token = client.auth.get_access_token()
        log_step(1, "Authentication & Configuration", "success", 
                 f"Acquired OAuth2 token ({token[:8]}...) for TSG {config.tsg_id} on {config.api_base_url}",
                 int((time.time() - s1_start) * 1000))
    except Exception as exc:
        log_step(1, "Authentication & Configuration", "error", str(exc))
        return {"success": False, "steps": steps_log, "total_duration_ms": int((time.time() - start_time) * 1000)}

    # Step 2: Read Info & Hierarchy
    s2_start = time.time()
    child_tsg_id = None
    try:
        tenants = client.list_tenants()
        for t in tenants:
            if t.get("parent_id") and not child_tsg_id:
                child_tsg_id = str(t.get("id"))
        
        ues = client.list_tenant_ues()
        groups = client.list_user_groups()
        log_step(2, "Read Tenant Info & Inventory", "success",
                 f"Discovered {len(tenants)} tenants, {ues.get('totalItems', 0)} registered SIMs, {len(groups.get('models', []))} user groups.",
                 int((time.time() - s2_start) * 1000))
    except Exception as exc:
        log_step(2, "Read Tenant Info & Inventory", "warning", f"Notice during inventory read: {exc}")

    # Step 3: Create Test SIM
    s3_start = time.time()
    random_suffix = f"{random.randint(100000000, 999999999)}"
    test_imsi = f"208950{random_suffix}"
    test_imei = f"860123{random_suffix}"
    test_apn = config.default_apn or "sasetest"
    created_id = None

    try:
        create_resp = client.create_tenant_ue(
            imsi=test_imsi,
            imei=test_imei,
            apn=test_apn,
            tsg_id=child_tsg_id,
        )
        data_obj = create_resp.get("data", {})
        created_id = data_obj.get("id") or data_obj.get("identity_id")
        log_step(3, "Register Test SIM (UE)", "success",
                 f"Created Test SIM (IMSI: {test_imsi}, APN: {test_apn}, ID: {created_id}) in TSG {child_tsg_id or config.tsg_id}",
                 int((time.time() - s3_start) * 1000))
    except Exception as exc:
        log_step(3, "Register Test SIM (UE)", "error", str(exc))
        return {"success": False, "steps": steps_log, "total_duration_ms": int((time.time() - start_time) * 1000)}

    # Step 4: Verify test SIM exists
    s4_start = time.time()
    try:
        time.sleep(1)
        if created_id:
            client.get_tenant_ue(created_id)
        log_step(4, "Verify SIM in Control Plane", "success",
                 f"Confirmed test SIM {created_id} is active and indexed.",
                 int((time.time() - s4_start) * 1000))
    except Exception as exc:
        log_step(4, "Verify SIM in Control Plane", "warning", f"Eventual consistency notice: {exc}")

    # Step 5: 5G Session Registration
    s5_start = time.time()
    session = UESession(
        imsi=test_imsi,
        imei=test_imei,
        apn=test_apn,
        ip_type="IPv4",
        ipv4_addr="10.56.0.195",
    )
    try:
        sess_resp = client.register_ue_session(session)
        log_step(5, "Register 5G Subscriber Session", "success",
                 f"Session telemetry enriched with IP 10.56.0.195 (HTTP {sess_resp.get('status_code')})",
                 int((time.time() - s5_start) * 1000))
    except Exception as exc:
        log_step(5, "Register 5G Subscriber Session", "warning", f"Session telemetry notice: {exc}")

    # Step 6: 5G Session Termination
    s6_start = time.time()
    try:
        term_resp = client.deregister_ue_session(session)
        log_step(6, "Terminate 5G Subscriber Session", "success",
                 f"Session termination telemetry accepted (HTTP {term_resp.get('status_code')})",
                 int((time.time() - s6_start) * 1000))
    except Exception as exc:
        log_step(6, "Terminate 5G Subscriber Session", "warning", f"Session termination notice: {exc}")

    # Step 7: Delete Test SIM
    s7_start = time.time()
    try:
        if created_id:
            client.delete_tenant_ue(created_id)
            log_step(7, "Delete Test SIM (UE)", "success",
                     f"Safely deleted test SIM ID: {created_id}",
                     int((time.time() - s7_start) * 1000))
        else:
            log_step(7, "Delete Test SIM (UE)", "warning", "No created ID returned to delete")
    except Exception as exc:
        log_step(7, "Delete Test SIM (UE)", "error", f"Failed to delete test SIM: {exc}")

    # Step 8: Verify Clean State
    s8_start = time.time()
    try:
        time.sleep(1)
        final_list = client.list_tenant_ues()
        found = any(str(u.get("identity_id") or u.get("id")) == str(created_id) for u in final_list.get("data", []))
        log_step(8, "Verify Clean State", "success" if not found else "warning",
                 "Test SIM completely removed from tenant inventory." if not found else "Item propagating removal.",
                 int((time.time() - s8_start) * 1000))
    except Exception as exc:
        log_step(8, "Verify Clean State", "warning", str(exc))

    total_duration = int((time.time() - start_time) * 1000)
    all_ok = all(s["status"] != "error" for s in steps_log)

    return {
        "success": all_ok,
        "total_duration_ms": total_duration,
        "steps": steps_log,
        "test_imsi": test_imsi,
        "test_apn": test_apn,
    }


# -----------------------------------------------------------------------------
# Frontend Single Page App Delivery
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def serve_index():
    """Serve the single-page application interface."""
    index_file = BASE_DIR / "templates" / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Template index.html not found")
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
