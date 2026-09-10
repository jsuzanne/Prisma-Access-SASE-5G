# Prisma SASE 5G Management & Lifecycle Portal

Web Application, REST API, CLI, and Python toolkit for Palo Alto Networks **Prisma SASE 5G** (Strata Cloud Manager & Telecom 5G Core Integration).

Enables full programmatic lifecycle management of User Equipment (UE / SIM Cards), real-time 5G session telemetry enrichment, subscriber user groups, monitoring KPI metrics, and automated end-to-end testing.

---

## 🌟 Key Features

- **5G SASE Summary Dashboard (Strata Cloud Manager Alignment)**:
  - **4 Top KPI Cards**: Total 5G Tenants, Total Bandwidth (Mbps), Total Configured Users, and 5G Network Interconnects (VLAN attachments Up/Down).
  - **Throughput Trend Chart**: Real-time dual-curve time-series monitoring with Ingress (Purple) and Egress (Cyan) bandwidth metrics over 1 hour, 24 hours, or 7 days with interactive hover tooltips.
- **SIM Cards & 5G Identities Management**:
  - **SCM-Style SIM Inventory**: Real-time table displaying IMSI, IMEI, APN, Tenant, Subscriber Groups, and Action buttons.
  - **Edit 5G Identity Side Drawer / Modal**: Change IMSI, IMEI, APN, and assign/move SIMs between subscriber security groups (`Permissive`, `Restrictive`, or custom groups).
- **5G Identity Groups Management & Zero-Trust Policies**:
  - **Create New Subscriber Groups**: Create custom policy groups (e.g. `VIP-Sensors`, `Field-Workers`, `Finance-eSIMs`) directly via `POST /mt/manage/5g/userGroup`.
  - **System Group Safeguards**: Built-in system groups (`Restrictive` and `Permissive`) are strictly protected with immutable locks against accidental deletion.
- **5G Session Telemetry (Control & User Plane Correlation)**:
  - Real-time IP allocation telemetry injection (`POST /mt/manage/5g/register/ue`) and graceful session termination (`POST /mt/manage/5g/deregister/ue`).
  - Correlates mobile IP with IMSI/IMEI identifiers for instant Zero-Trust policy enforcement without endpoint agents.
- **In-App Settings & Credentials Manager**:
  - Manage service account credentials (`PANW_CLIENT_ID`, `PANW_CLIENT_SECRET`, `PANW_TSG_ID`, `DEFAULT_APN`) directly from the Web UI with security masking and a live connection test button.
- **3-Pillars Guide (SCM & CLI Matrix)**:
  - Interactive reference mapping every lifecycle action across **Web UI**, **CLI commands**, and **Strata Cloud Manager navigation paths**.
- **Automated Lifecycle Runner**:
  - Interactive 8-step pipeline with live terminal log for end-to-end testing.
- **Production-Ready & CI/CD**:
  - Containerized with Docker (`jsuzanne/prisma-5g-sase:latest`), verified with 32 unit tests on GitHub Actions.

---

## 🚀 Quick Start with Docker Compose

The easiest way to run the portal on any machine:

### Option A: 1-Click Launch with `docker-compose.yml`

Create a `docker-compose.yml` file with the following contents:

```yaml
services:
  prisma-sase-5g:
    image: jsuzanne/prisma-5g-sase:latest
    container_name: prisma-sase-5g
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

Then start the container:

```bash
# Start container in detached mode (zero config needed)
docker compose up -d
```

### Option B: Clone Repository & Run

```bash
# 1. Clone repository
git clone git@github.com:jsuzanne/Prisma-SASE-5G.git
cd Prisma-SASE-5G

# 2. Start container with Docker Compose
docker compose up -d
```

### Option C: Direct `docker run`

```bash
docker run -d -p 8000:8000 --name prisma-sase-5g jsuzanne/prisma-5g-sase:latest
```

Once running, open your browser at **[http://localhost:8000](http://localhost:8000)**.
Credentials and tenant settings can be configured directly via the Web UI in the **Settings** tab or in a local `.env` file.

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

Provisioning a 5G subscriber into Palo Alto Networks Prisma SASE 5G consists of two essential phases:
1. **Control Plane Provisioning**: Mapping the SIM hardware identifiers (`IMSI`, `IMEI`, `APN`) and assigning security groups.
2. **User Plane / Session Enrichment**: Injecting real-time IP allocation telemetry when the SIM connects to the 5G Core network, binding Zero-Trust security policies instantly.

Below is the step-by-step lifecycle breakdown across the **Web UI**, the **CLI**, and **Strata Cloud Manager (SCM)**:

---

### Step 1: Monitor 5G SASE Health & Interconnects

Inspect the global health of your 5G SASE tenant, allocated bandwidth, and VLAN attachments.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | Navigate to the **"5G SASE Summary"** tab to view the 4 KPI cards and Ingress/Egress Throughput trends. |
| 💻 **CLI** | `python3 manage_5g.py summary` and `python3 manage_5g.py interconnect` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Dashboard** $\to$ **5G SASE Summary**.<br>Displays regional interconnects, active compute region (e.g. `europe-west9`), and VLAN health. |

---

### Step 2: Manage 5G Identity Groups (Security Policies)

Inspect or create subscriber security groups that hold Zero-Trust policy profiles (e.g. `Restrictive`, `Permissive`, `VIP-Sensors`).

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"Groups & Policies"** tab, click **"+ Add Group"** to define a new policy group. Existing system groups (`Restrictive`, `Permissive`) are protected against accidental deletion. |
| 💻 **CLI** | `python3 manage_5g.py groups`<br>`python3 manage_5g.py group-create --name "VIP-Sensors" --tsg-id 1291887562` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Objects** $\to$ **5G Identities Groups** (or **Mobile Security** $\to$ **Subscriber Groups**).<br>Click **+ Add** to define group rules. |

---

### Step 3: Provision a SIM Card / UE (Control Plane)

Register the SIM card hardware identifiers and assign it to an APN (default `sasetest`) and target Tenant Service Group.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | Click **"Add New SIM"** in the banner or **SIM Inventory** tab, enter or generate IMSI/IMEI, select APN `sasetest`, and click **"Create SIM"**. |
| 💻 **CLI** | `python3 manage_5g.py add --imsi 208950123456789 --imei 860123123456789 --apn sasetest` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Configuration** $\to$ **Mobile Security** $\to$ **5G Identities (UE)**.<br>Click **+ Add New** to enter IMSI, IMEI, and APN. |

---

### Step 4: Edit SIM & Assign Subscriber Group

Assign or move the SIM card to a specific security policy group (`Permissive`, `Restrictive`, etc.).

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"SIM Inventory"** tab, click the **Edit ✏️** button on any SIM row (or click its group badge). In the **Edit 5G Identity** drawer, choose the desired **Subscriber Group** and click **Save**. |
| 💻 **CLI** | `python3 manage_5g.py assign-group --ue-id "<IDENTITY_ID>" --group-name "Permissive"`<br>`python3 manage_5g.py update "<IDENTITY_ID>" --apn "sase" --group-id "<GROUP_ID>"` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Configuration** $\to$ **5G Identities** $\to$ Click the pencil icon on the subscriber $\to$ In **Edit 5G Identity**, update the group assignment $\to$ Click **Save**. |

---

### Step 5: Activate 5G Session Telemetry (IP Allocation / Data Plane)

When the IoT device or mobile tablet connects to the 5G Core network, the carrier/telecom network assigns an IP address (e.g., `10.56.0.195`). The 5G Core automatically notifies Prisma SASE 5G via the REST telemetry endpoint to bind security policies in real time without any device agent or VPN client.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"SIM Inventory"** tab, click **"Connect 5G"** next to the SIM (or use the form in the **"5G Sessions"** tab). |
| 💻 **CLI** | `python3 manage_5g.py session-register --imsi 208950123456789 --imei 860123123456789 --apn sasetest --ipv4 10.56.0.195` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Activity / Monitor** $\to$ **User Activity** (or **Traffic Logs**).<br>Traffic from IP `10.56.0.195` is automatically correlated with the subscriber IMSI, applying the security rule associated with its Subscriber Group (`Permissive` vs `Restrictive`). |

---

### Step 6: Threat Inspection & Policy Enforcement in SCM

When a device in the `Restrictive` group attempts to access malicious or unauthorized content (e.g. `wicar.org` or streaming services):

| Component | Observation & Behavior |
| :--- | :--- |
| 📱 **Connected Device** | The browser receives the Palo Alto Networks **Zero-Trust Block Page** directly from the 5G Core user plane without requiring any local endpoint agent. |
| 🛡️ **Strata Cloud Manager (SCM)** | **Activity** $\to$ **Threat Logs** & **URL Filtering Logs**.<br>Log entry displays: **Source User**: `IMSI 208950...`, **Source IP**: `10.56.0.195`, **URL**: `wicar.org`, **Action**: `block-url`, **Rule**: `Block-High-Risk-IoT`. |

---

### Step 7: Terminate / Disconnect 5G Session

When the subscriber disconnects or changes cell/IP, a deregistration event is emitted.

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"5G Sessions"** tab, send a session termination event. |
| 💻 **CLI** | `python3 manage_5g.py session-terminate --imsi 208950123456789 --imei 860123123456789 --apn sasetest --ipv4 10.56.0.195` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Activity** $\to$ **Session Monitor**.<br>The active IP session mapping is gracefully aged out and unlinked from the IMSI. |

---

### Step 8: Deprovision / Delete SIM Card

To decommission or remove a SIM from the tenant:

| Method | How to Perform / Where to View |
| :--- | :--- |
| 🌐 **Web UI** | In the **"SIM Inventory"** tab, click **"Delete"** next to the test SIM. |
| 💻 **CLI** | `python3 manage_5g.py delete <IDENTITY_ID>` |
| 🛡️ **Strata Cloud Manager (SCM)** | **Configuration** $\to$ **Mobile Security** $\to$ **5G Subscribers**.<br>The record is purged from the tenant's active SIM database. |

---

## 🛠️ Complete CLI Command Reference (`manage_5g.py`)

```bash
# Tenants & Hierarchy
python3 manage_5g.py tenants

# SIM / UE Inventory
python3 manage_5g.py list
python3 manage_5g.py get <IDENTITY_ID>
python3 manage_5g.py add --imsi <IMSI> --imei <IMEI> --apn sasetest
python3 manage_5g.py update <IDENTITY_ID> --apn sase --group-id <GROUP_ID>
python3 manage_5g.py delete <IDENTITY_ID>
python3 manage_5g.py bulk-delete <ID_1> <ID_2>

# 5G Subscriber Groups
python3 manage_5g.py groups
python3 manage_5g.py group-get <GROUP_ID>
python3 manage_5g.py group-create --name "VIP-Sensors" --tsg-id 1291887562
python3 manage_5g.py assign-group --ue-id <IDENTITY_ID> --group-name "Permissive"
python3 manage_5g.py group-delete <CUSTOM_GROUP_ID>

# 5G Real-time Session Telemetry
python3 manage_5g.py session-register --imsi <IMSI> --imei <IMEI> --apn sasetest --ipv4 10.56.0.195
python3 manage_5g.py session-terminate --imsi <IMSI> --imei <IMEI> --apn sasetest --ipv4 10.56.0.195

# SCM Monitoring KPIs & Interconnects
python3 manage_5g.py summary
python3 manage_5g.py interconnect
```

---

## 🧪 Automated Testing & Verification

Run the test suite covering all REST endpoints, authentication, SIM CRUD, group creation, group assignment, and system protections:

```bash
# Run unit tests (25 passing tests)
./.venv/bin/python -m unittest discover tests

# Run end-to-end automated lifecycle script
python3 test_lifecycle.py
```

---

## 📡 REST API Documentation

Interactive Swagger documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status` | System health, TSG status, and token preview |
| `GET` | `/api/config` | Read current configuration (masked secret) |
| `POST` | `/api/config` | Update `.env` credentials dynamically |
| `POST` | `/api/config/test` | Test OAuth2 connection & tenant resolution |
| `GET` | `/api/tenants` | List tenant hierarchy (Root MSP and child TSGs) |
| `GET` | `/api/ues` | List registered SIM cards with group policies |
| `POST` | `/api/ues` | Register new SIM card (optional session IP attach) |
| `PUT` | `/api/ues/{id}` | Update SIM metadata and group assignment |
| `PUT` | `/api/ues/{id}/group` | Assign SIM to a specific subscriber group |
| `DELETE` | `/api/ues/{id}` | Safely delete a SIM card mapping |
| `GET` | `/api/groups` | Query subscriber security user groups |
| `POST` | `/api/groups` | Create a new 5G subscriber identity group |
| `GET` | `/api/groups/{id}` | Get group details and member identity list |
| `PUT` | `/api/groups/{id}` | Update group name or member list |
| `DELETE` | `/api/groups/{id}` | Delete a subscriber group (system groups protected) |
| `POST` | `/api/sessions/register` | Send 5G session attach / IP telemetry event |
| `POST` | `/api/sessions/deregister` | Send 5G session terminate event |
| `GET` | `/api/metrics/summary` | 5G SASE Summary KPI stats (Tenants, Bandwidth, Configured Users, Interconnects) |
| `GET` | `/api/metrics/throughput` | Real-time Ingress & Egress Throughput Trend time-series points |
| `POST` | `/api/lifecycle/run` | Execute full 8-step lifecycle test pipeline |

---

## 🔒 Security & Protection Policies

- **Protected System Groups**: The built-in security profiles (`Restrictive` and `Permissive`) are locked against accidental deletion via the UI, API, and CLI.
- **Credential Privacy**: `.env` is ignored by `.gitignore` and `.dockerignore`. Client secrets are masked in the UI and never exposed in client-side responses.
- **Production Safety**: Existing production SIMs and configurations are preserved. Test creations default to the isolated APN `sasetest`.

---

## 📖 References

- [Configure Prisma SASE 5G Documentation](https://docs.paloaltonetworks.com/sase/prisma-sase-multitenant-platform/manage-sase-5g/config-sase-5g)
- [Palo Alto Networks pan.dev SASE 5G API Reference](https://pan.dev/sase/api/manage-services-5g/post-mt-manage-5-g-register-ue/)
