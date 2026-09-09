# Prisma Access 5G SASE Management & Lifecycle Portal

Web Application, REST API, CLI, and Python toolkit for Palo Alto Networks **Prisma Access 5G SASE** (Strata Cloud Manager & Telecom 5G Core Integration).

Enables full programmatic lifecycle management of User Equipment (UE / SIM Cards), real-time 5G session telemetry enrichment, subscriber user groups, and automated end-to-end testing.

---

## 🌟 Key Features

- **Modern Web Interface & REST API (FastAPI)**:
  - **Full SIM Lifecycle**: Real-time inventory table of SIM cards, tenant hierarchy mapping, and group policy badges (`Permissive`, `Restrictive`).
  - **5G Session Controller**: Real-time IP telemetry injection (`POST /mt/manage/5g/register/ue`) and termination (`POST /mt/manage/5g/deregister/ue`).
  - **Automated Lifecycle Runner**: Interactive 8-step test suite with live visual pipeline and execution terminal log.
  - **In-App Settings**: Dynamic credentials management interface allowing updating and live testing of `.env` configuration.
- **Agentless Zero-Trust Security**: No VPN agent or client required on IoT/mobile endpoints. Security policy enforcement is directly embedded into the 5G Core user plane.
- **Docker Containerized**: Production-ready container based on `python:3.11-slim`, running with `docker compose up --build`.
- **CI/CD Built-in**: GitHub Actions workflow (`.github/workflows/ci.yml`) for automated unit tests and Docker image validation & publishing.

---

## 🚀 Quick Start with Docker

The fastest way to run the portal:

```bash
# 1. Clone repository
git clone git@github.com:jsuzanne/Prisma-Access-SASE-5G.git
cd Prisma-Access-SASE-5G

# 2. Copy and configure your environment (optional if configured via Web UI Settings)
cp .env.example .env

# 3. Start with Docker Compose
docker compose up --build
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 💻 Local Development (Without Docker)

### 1. Installation

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials (`.env`)

```ini
PANW_CLIENT_ID=your-service-account-client-id
PANW_CLIENT_SECRET=your-secret-here
PANW_TSG_ID=your-root-tsg-id
PANW_API_BASE_URL=https://api.sase.paloaltonetworks.com
PANW_AUTH_URL=https://auth.apps.paloaltonetworks.com/am/oauth2/access_token
DEFAULT_APN=sasetest
DEFAULT_IP_TYPE=IPv4
```

*(You can also configure these settings directly in the Web UI via the Settings modal).*

### 3. Launch Web Application

```bash
python3 app.py
```
Visit **[http://localhost:8000](http://localhost:8000)**.

---

## 🛠 CLI Usage (`manage_5g.py`)

```bash
# List registered SIM cards
python3 manage_5g.py list

# Add test SIM card with APN sasetest
python3 manage_5g.py add --imsi 208950123456789 --imei 860123123456789 --apn sasetest

# Add SIM card AND immediately activate real-time 5G session with IP:
python3 manage_5g.py add --imsi 208950123456789 --imei 860123123456789 --apn sasetest --ip 10.56.0.195

# Register 5G session telemetry
python3 manage_5g.py session-register --imsi 208950123456789 --imei 860123123456789 --apn sasetest --ipv4 10.56.0.195

# Terminate 5G session
python3 manage_5g.py session-terminate --imsi 208950123456789 --imei 860123123456789 --apn sasetest

# Delete SIM card mapping
python3 manage_5g.py delete <IDENTITY_ID>

# List subscriber user groups
python3 manage_5g.py groups
```

---

## 🧪 Automated Lifecycle Test Suite

Run the full end-to-end automated verification script:

```bash
python3 test_lifecycle.py
```

Or run unit tests:

```bash
python3 -m unittest discover tests
```

---

## 📡 REST API Documentation

FastAPI provides automatic interactive Swagger documentation at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | System health, TSG status, and token preview |
| `GET` | `/api/config` | Read current configuration (masked secret) |
| `POST` | `/api/config` | Update `.env` credentials dynamically |
| `POST` | `/api/config/test` | Test OAuth2 connection & tenant resolution |
| `GET` | `/api/tenants` | List tenant hierarchy (Root MSP and child TSGs) |
| `GET` | `/api/ues` | List registered SIM cards with group policies |
| `POST` | `/api/ues` | Register new SIM card (optional session IP attach) |
| `DELETE` | `/api/ues/{id}` | Safely delete a SIM card mapping |
| `GET` | `/api/groups` | Query subscriber security user groups |
| `POST` | `/api/sessions/register` | Send 5G session attach / IP telemetry event |
| `POST` | `/api/sessions/deregister` | Send 5G session terminate event |
| `POST` | `/api/lifecycle/run` | Execute full 8-step lifecycle test pipeline |

---

## 🔒 Security & Privacy

- Credentials in `.env` are strictly ignored by `.gitignore` and `.dockerignore`.
- Secrets are masked in the UI and never exposed in client-side responses.
- The web application protects existing production SIM cards in configured tenant service groups.

---

## 📖 References

- [Configure Prisma SASE 5G Documentation](https://docs.paloaltonetworks.com/sase/prisma-sase-multitenant-platform/manage-sase-5g/config-sase-5g)
- [Palo Alto Networks pan.dev SASE 5G API Reference](https://pan.dev/sase/api/manage-services-5g/post-mt-manage-5-g-register-ue/)
