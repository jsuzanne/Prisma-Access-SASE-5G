# Prisma Access 5G SASE Management Client

Python toolkit and CLI interface for Palo Alto Networks **Prisma Access 5G SASE** (Strata Cloud Manager), enabling programmatic lifecycle management of User Equipment (UE / SIM Cards), real-time session telemetry enrichment, and subscriber user groups.

---

## 🌟 Key Features

- **Automated Authentication**: Seamless OAuth2 token generation and caching via PANW Cloud Identity Engine (`client_credentials` grant with auto-refresh on 15-minute token expiry), plus static Bearer token support.
- **Tenant UE / SIM Management (CRUD)**:
  - **List & Search**: Paginated query of registered SIM cards / UEs (`POST /mt/manage/5g/tenantUEInfo/list`).
  - **Add SIM**: Register new IMSI/IMEI/APN mappings (`POST /mt/manage/5g/tenantUEInfo`).
  - **Get Details**: Retrieve specific UE metadata (`GET /mt/manage/5g/tenantUEInfo/{id}`).
  - **Update**: Update IMSI/IMEI/APN mappings (`PUT /mt/manage/5g/tenantUEInfo/{id}`).
  - **Delete**: Remove single or bulk UE records (`DELETE /mt/manage/5g/tenantUEInfo/{id}`).
- **Real-Time Session Enrichment**:
  - **Register Session**: Send real-time subscriber attach/IP allocation telemetry (`POST /mt/manage/5g/register/ue`).
  - **Terminate Session**: Send session disconnect events (`POST /mt/manage/5g/deregister/ue`).
- **Interactive CLI & End-to-End Test Suite**:
  - `manage_5g.py`: Full-featured CLI with rich formatted tables and JSON export.
  - `test_lifecycle.py`: Automated 8-step test workflow (Authenticate -> Read -> Add -> Verify -> Session Start -> Session Stop -> Delete -> Clean Verify).

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or open workspace
cd "Prisma Access 5G SASE"

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials (`.env`)

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your Palo Alto Networks credentials:

```ini
# PANW Strata Cloud Manager Service Account Credentials
PANW_CLIENT_ID=your_service_account_client_id
PANW_CLIENT_SECRET=your_service_account_client_secret
PANW_TSG_ID=your_tenant_service_group_id

# Optional: If you already have a pre-generated Bearer Token
# PANW_AUTH_TOKEN=your_bearer_token

# Endpoints (Defaults)
PANW_API_BASE_URL=https://stratacloudmanager.paloaltonetworks.com
PANW_AUTH_URL=https://auth.apps.paloaltonetworks.com/am/oauth2/access_token
DEFAULT_APN=internet.panw.com
```

---

## 🛠 CLI Usage (`manage_5g.py`)

### 1. List Registered SIM Cards / UEs
```bash
python3 manage_5g.py list
```
*Output in JSON format:*
```bash
python3 manage_5g.py list --json
```

### 2. Add / Map a New SIM Card (With Optional 5G Session Activation)
```bash
# Map SIM card to a tenant:
python3 manage_5g.py add --imsi 208950123456789 --imei 860123123456789 --apn sase --tenant "Transatel demo"

# Map SIM card AND immediately activate real-time 5G session with IP:
python3 manage_5g.py add --imsi 208950123456789 --imei 860123123456789 --apn sase --tenant "Transatel demo" --ip 10.56.0.196
```

### 3. Get Details of a SIM Card
```bash
python3 manage_5g.py get <IDENTITY_ID>
```

### 4. Delete a SIM Card Mapping
```bash
python3 manage_5g.py delete <IDENTITY_ID>
```

### 5. Send Real-Time Session Telemetry (Enrichment)
```bash
# Session Start / Attach
python3 manage_5g.py session-register --imsi 208950123456789 --imei 860123123456789 --apn internet.panw.com --ipv4 10.45.0.25

# Session Terminate / Disconnect
python3 manage_5g.py session-terminate --imsi 208950123456789 --imei 860123123456789 --apn internet.panw.com
```

### 6. List 5G Subscriber User Groups
```bash
python3 manage_5g.py groups
```

---

## 🧪 Automated End-to-End Lifecycle Test

Run the complete test lifecycle script to verify authentication, read current state, add 1 test user, verify, simulate 5G session telemetry, and delete the user:

```bash
python3 test_lifecycle.py
```

---

## 🐍 Python SDK Example

```python
from src.config import load_config
from src.client import Prisma5GClient
from src.models import UESession

# 1. Initialize client
config = load_config()
client = Prisma5GClient(config)

# 2. List all SIMs / UEs
ues = client.list_tenant_ues()
print(f"Total UEs: {ues.get('totalItems')}")

# 3. Add a new SIM card
created = client.create_tenant_ue(
    imsi="208950123456789",
    imei="860123123456789",
    apn="internet.panw.com"
)
identity_id = created["data"]["id"]
print(f"Created UE ID: {identity_id}")

# 4. Trigger 5G real-time session event
session = UESession(
    imsi="208950123456789",
    imei="860123123456789",
    apn="internet.panw.com",
    ip_type="IPV4",
    ipv4_addr="10.45.0.25"
)
client.register_ue_session(session)

# 5. Delete SIM card mapping
client.delete_tenant_ue(identity_id)
print("Deleted test SIM.")
```

---

## 📚 API Endpoints Implemented

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/mt/manage/5g/tenantUEInfo/list` | List/search tenant SIM mappings |
| `POST` | `/mt/manage/5g/tenantUEInfo` | Create new tenant SIM mapping |
| `GET` | `/mt/manage/5g/tenantUEInfo/{ueInfoId}` | Get single tenant UE mapping |
| `PUT` | `/mt/manage/5g/tenantUEInfo/{identity_id}` | Update tenant UE mapping |
| `DELETE` | `/mt/manage/5g/tenantUEInfo/{identity_id}` | Delete tenant UE mapping |
| `POST` | `/mt/manage/5g/tenantUEInfo/delete` | Bulk delete tenant UE mappings |
| `POST` | `/mt/manage/5g/register/ue` | Register real-time 5G UE session |
| `POST` | `/mt/manage/5g/deregister/ue` | Terminate real-time 5G UE session |
| `POST` | `/mt/manage/5g/userGroup/list` | Query tenant subscriber user groups |
| `POST` | `/mt/manage/5g/cie/token` | Save Cloud Identity Engine token |
| `POST` | `/mt/manage/5g/cie/token/details` | Fetch CIE token metadata |

---

## 📖 References
- [Configure Prisma SASE 5G Documentation](https://docs.paloaltonetworks.com/sase/prisma-sase-multitenant-platform/manage-sase-5g/config-sase-5g)
- [Palo Alto Networks pan.dev SASE 5G API Reference](https://pan.dev/sase/api/manage-services-5g/post-mt-manage-5-g-register-ue/)
