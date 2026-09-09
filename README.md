# Prisma Access 5G SASE Management & Lifecycle Portal

Web Application, REST API, CLI, and Python toolkit for Palo Alto Networks **Prisma Access 5G SASE** (Strata Cloud Manager & Telecom 5G Core Integration).

Enables full programmatic lifecycle management of User Equipment (UE / SIM Cards), real-time 5G session telemetry enrichment, subscriber user groups, and automated end-to-end testing.

---

## 🌟 Key Features

- **Modern Web Interface & REST API (FastAPI)**:
  - **Full SIM Lifecycle**: Real-time inventory table of SIM cards, tenant hierarchy mapping, and group policy badges (`Permissive`, `Restrictive`).
  - **In-App Settings & Credentials**: Complete Settings tab & modal to view, edit, and test `.env` credentials in real time with security masking.
  - **5G Session Controller**: Real-time IP telemetry injection (`POST /mt/manage/5g/register/ue`) and termination (`POST /mt/manage/5g/deregister/ue`).
  - **Automated Lifecycle Runner**: Interactive 8-step test suite with live visual pipeline and execution terminal log.
- **Agentless Zero-Trust Security**: No VPN agent or client required on IoT/mobile endpoints. Security policy enforcement is directly embedded into the 5G Core user plane.
- **Docker Containerized**: Production-ready container based on `python:3.11-slim`, running with `docker compose up --build`.
- **CI/CD Built-in**: GitHub Actions workflow (`.github/workflows/ci.yml`) for automated unit tests and Docker image validation & publishing to Docker Hub (`jsuzanne/prisma-5g-sase:latest`).

---

## 🚀 Quick Start with Docker

The fastest way to run the portal:

```bash
# 1. Clone repository
git clone git@github.com:jsuzanne/Prisma-Access-SASE-5G.git
cd Prisma-Access-SASE-5G

# 2. Start with Docker (Image pulled directly from Docker Hub)
docker run -d -p 8000:8000 --name prisma-5g-sase jsuzanne/prisma-5g-sase:latest
```

Or build locally with Docker Compose:
```bash
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

### 2. Configure Credentials (`.env` or via Web UI)

You can configure credentials directly in the Web UI (**Settings & Credentials** tab), or create `.env`:

```ini
PANW_CLIENT_ID=5g-ue-registration@1965438697.iam.panserviceaccount.com
PANW_CLIENT_SECRET=your-secret-here
PANW_TSG_ID=1965438697
PANW_API_BASE_URL=https://api.sase.paloaltonetworks.com
PANW_AUTH_URL=https://auth.apps.paloaltonetworks.com/am/oauth2/access_token
DEFAULT_APN=sasetest
DEFAULT_IP_TYPE=IPv4
```

### 3. Launch Web Application

```bash
python3 app.py
```
Visit **[http://localhost:8000](http://localhost:8000)**.

---

## 📖 Complete Provisioning Walkthrough: Web UI vs CLI vs Strata Cloud Manager (SCM)

Provisioning a 5G subscriber into Palo Alto Networks Prisma Access 5G SASE consists of two essential phases:
1. **Control Plane Provisioning**: Mapping the SIM hardware identifiers (`IMSI`, `IMEI`, `APN`) to a specific Tenant Service Group (TSG).
2. **User Plane / Session Enrichment**: Injecting real-time IP allocation telemetry when the SIM connects to the 5G Core network, binding Zero-Trust security policies instantly.

Below is the step-by-step lifecycle breakdown across the **Web UI**, the **CLI**, and **Strata Cloud Manager (SCM)**:

---

### Step 1: Discover Tenants and Security Groups

Inspect your organization's hierarchy and available subscriber security profiles (e.g. `Permissive`, `Restrictive`).

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | Navigate to the **"Groups & Policies"** tab to view all subscriber groups and their member counts. |
| 💻 **CLI** | Run `python3 manage_5g.py tenants` to view TSGs, and `python3 manage_5g.py groups` to view subscriber groups. |
| 🛡️ **Strata Cloud Manager (SCM)** | **Top Navigation** $\to$ Select Tenant / TSG Hierarchy.<br>**Configuration** $\to$ **Mobile Security** $\to$ **Subscriber Groups** (or **Objects** $\to$ **User Groups**). |

---

### Step 2: Provision a SIM Card / UE (Control Plane)

Register the SIM card hardware identifiers and assign it to an APN (default `sasetest`) and target Tenant Service Group.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | Click **"Add Test SIM"** in the top right banner, enter or generate IMSI/IMEI, select APN `sasetest`, and click **"Create SIM"**. |
| 💻 **CLI** | `python3 manage_5g.py add --imsi 208950123456789 --imei 860123123456789 --apn sasetest` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Configuration** $\to$ **Mobile Security** $\to$ **5G Subscribers / User Equipment (UE)**.<br>The newly provisioned SIM appears with its assigned IMSI, IMEI, and APN. |

---

### Step 3: Verify Provisioning in SASE Control Plane

Confirm that the subscriber identity is active and indexed across the management plane.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | Open the **"SIM Inventory"** tab. The new SIM is listed with its IMSI, IMEI, APN, and associated group badge. |
| 💻 **CLI** | Run `python3 manage_5g.py get <IDENTITY_ID>` or list all registered UEs with `python3 manage_5g.py list`. |
| 🛡️ **Strata Cloud Manager (SCM)** | **Configuration** $\to$ **Mobile Security** $\to$ **Tenant UEs**.<br>Filter by IMSI or IMEI to inspect the provisioned record. |

---

### Step 4: Activate 5G Session Telemetry (IP Allocation / Data Plane)

When the IoT device or mobile tablet connects to the 5G Core network, the carrier/telecom network assigns an IP address (e.g., `10.56.0.195`). The 5G Core automatically notifies Prisma Access SASE via the REST telemetry endpoint to bind security policies in real time without any device agent or VPN client.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"SIM Inventory"** tab, click **"Connect 5G"** next to the SIM (or use the form in the **"5G Sessions"** tab). |
| 💻 **CLI** | `python3 manage_5g.py session-register --imsi 208950123456789 --imei 860123123456789 --apn sasetest --ipv4 10.56.0.195` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Activity / Monitor** $\to$ **User Activity** (or **Traffic Logs**).<br>Traffic from IP `10.56.0.195` is automatically correlated with the subscriber IMSI, applying the security rule associated with its Subscriber Group (`Permissive` vs `Restrictive`). |

---

### Step 5: Threat Inspection & Policy Enforcement in SCM

When a device in the `Restrictive` group attempts to access malicious or unauthorized content (e.g. `wicar.org` or streaming services):

| Component | Observation & Behavior |
| :--- | :--- |
| 📱 **Connected Device** | The browser receives the Palo Alto Networks **Zero-Trust Block Page** directly from the 5G Core user plane without requiring any local endpoint agent. |
| 🛡️ **Strata Cloud Manager (SCM)** | **Activity** $\to$ **Threat Logs** & **URL Filtering Logs**.<br>Log entry displays: **Source User**: `IMSI 208950...`, **Source IP**: `10.56.0.195`, **URL**: `wicar.org`, **Action**: `block-url`, **Rule**: `Block-High-Risk-IoT`. |

---

### Step 6: Terminate / Disconnect 5G Session

When the subscriber disconnects or changes cell/IP, a deregistration event is emitted.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"5G Sessions"** tab, send a session termination event. |
| 💻 **CLI** | `python3 manage_5g.py session-terminate --imsi 208950123456789 --imei 860123123456789 --apn sasetest --ipv4 10.56.0.195` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Activity** $\to$ **Session Monitor**.<br>The active IP session mapping is gracefully aged out and unlinked from the IMSI. |

---

### Step 7: Deprovision / Delete SIM Card

To decommission or remove a SIM from the tenant:

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"SIM Inventory"** tab, click **"Delete"** next to the test SIM. |
| 💻 **CLI** | `python3 manage_5g.py delete <IDENTITY_ID>` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Configuration** $\to$ **Mobile Security** $\to$ **5G Subscribers**.<br>The record is purged from the tenant's active SIM database. |

---

## 🧪 Automated Lifecycle Test Suite

Run the full end-to-end automated verification script:

```bash
python3 test_lifecycle.py
```

Or run Python unit tests:

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
| `GET` | `/api/metrics/summary` | 5G SASE Summary KPI stats (Tenants, Bandwidth, Configured Users, Interconnects) |
| `GET` | `/api/metrics/throughput` | Real-time Ingress & Egress Throughput Trend time-series points |
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
