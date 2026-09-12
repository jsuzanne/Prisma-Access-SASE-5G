# 5G Zero-Trust Subscriber Security Groups & Quarantine Architecture

> **Guide for Field Solution Architects, MSSPs, and Enterprise SecOps Teams**  
> Integrated with **Palo Alto Networks Prisma SASE 5G** and **Telecom / Private 5G Core Networks**.

---

## 1. Overview & Agentless Zero-Trust 5G Concept

In traditional enterprise IT, security policies (User-ID, ZTNA) rely on software agents installed on end-user endpoints (e.g. GlobalProtect). 

In **Cellular 5G IoT and Industry 4.0 environments**, hundreds of connected devices (EV chargers, factory AGVs, POS payment terminals, smart grid meters) run closed firmware or embedded operating systems where installing a security agent is impossible.

**Prisma SASE 5G** achieves **Agentless Zero-Trust**:
* The **5G Core UPF / Data Plane** authenticates the subscriber SIM (IMSI).
* Real-time session telemetry (`ueSession/register`) maps the dynamic IPv4/IPv6 address to the SIM Identity.
* **Subscriber Policy Groups** dynamically bind security policies (Threat Prevention, DNS Security, App-ID inspection, Lateral Movement Blocking) directly to the subscriber session in the Prisma SASE enforcement dataplane.

```
+-----------------------------------------------------------------------------------+
|                        5G ZERO-TRUST POLICY ENFORCEMENT                           |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [SIM Card / UE]                                                                  |
|   IMSI: 901370001420683                                                           |
|   IP:   10.56.0.201       ──> [5G Core UPF] ──> [Prisma SASE Security Dataplane] |
|   APN:  sasetest                                        │                         |
|                                                         ▼                         |
|  [Dynamic Policy Group]                   +───────────────────────────+           |
|   Group: "PCI-DSS-Payment-Terminals"  ──> | Allowed:  Bank TLS 1.3    |           |
|   (or "Threat-Quarantine-Isolation")      | Blocked:  Lateral / C2 IP |           |
|                                           +───────────────────────────+           |
+-----------------------------------------------------------------------------------+
```

---

## 2. The "Seed / Dummy SIM" Quarantine Architecture

### 2.1 The Challenge
When creating a 5G User Group via the SCM 5G Management API (`POST /mt/manage/5g/userGroup/create`), the API requires a **non-empty list of subscriber identities** (`identity_ids` with at least 1 SIM). 

In an incident response scenario, creating a Quarantine group from scratch *after* a threat is detected introduces unwanted operational friction and compile latency.

### 2.2 The Seed SIM Solution
To enable **instant, 1-click quarantine containment**:
1. **Pre-Create the Group with a Seed / Dummy SIM**:
   * Group Name: `IoT-Quarantine-Isolation`
   * Seed SIM IMSI: `901370000000000` (Named: `[SEED] Quarantine Placeholder`)
2. **Pre-Compile the SCM Firewall Rule**:
   * Security Rule: *Block all corporate lateral movement + Block internet access + Log high-severity alert to SOC / SIEM*.
   * Rule is pre-compiled and active on the firewall dataplane 24/7.
3. **Instant Containment in 1 Click**:
   * As soon as an IoT device (e.g. smart camera or EV charger) displays abnormal port scanning or lateral traffic, the SOC analyst moves the real SIM into `IoT-Quarantine-Isolation`.
   * The **Fast-Path Session Re-Anchor** immediately isolates the infected device in **< 2 seconds** without dropping cellular carrier connection (allowing remote forensic analysis).

---

## 3. Recommended Enterprise 5G Security Profiles

Here is the standardized catalog of recommended 5G Subscriber Security Groups:

| Icon | Security Group Name | Intended Use Case | Prisma SASE Security Profile |
|---|---|---|---|
| 🛡️ | **`IoT-Quarantine-Isolation`** | Compromised devices, infected nodes, abnormal scan alerts. | **Deny All** lateral & internet traffic. Allow TLS capture to SOC forensic server only. |
| 🔄 | **`IoT-Firmware-Update-OTA`** | EV chargers, meters, or vehicles during active firmware upgrades. | Temporarily allow specific cloud repositories (AWS S3, Azure Blob, GitHub). Block internal DBs. |
| 🏭 | **`OT-Industrial-Critical`** | AGV robots, Siemens/Schneider PLCs, factory automation. | **Zero-Trust Strict**: Allow SCADA/MES ports (Modbus TCP 502, OPC-UA 4840). Block all public internet. |
| 💳 | **`PCI-DSS-Payment-Terminals`** | Retail smart POS (Ingenico, Verifone), self-checkout kiosks. | **PCI-DSS Compliant**: Exclusively allow Bank acquisition gateways (TLS 1.3). Block peer-to-peer traffic. |
| 📡 | **`SmartGrid-Telemetry-LowPower`** | Smart water, gas, electricity meters, environmental sensors. | Allow lightweight IoT protocols (MQTT, CoAP, UDP). Enforce rate-limiting against volumetric DDoS. |
| 📱 | **`Field-Worker-Mobility`** | Maintenance technician iPads, airline ground crew, fleet drivers. | Corporate SaaS (Salesforce, Teams, O365) + DNS Security + Advanced URL Anti-Phishing. |

---

## 4. Strata Cloud Manager (SCM) IAM Roles & Permissions Analysis

### 4.1 What the `Multitenant Superuser` Role Delivers
In Strata Cloud Manager / CSP, when the Service Account is assigned:
* **Scope**: `All Apps & Services`
* **Role**: `Multitenant Superuser` on the Parent TSG (`SP-5G-POC2-Transatel` / TSG ID `1965438697`)

```
+-----------------------------------------------------------------------------------+
|               ROOT TSG: SP-5G-POC2-Transatel (TSG ID: 1965438697)                 |
|               Service Account: 5g-ue-registration [Multitenant Superuser]         |
+----------------------------------------+------------------------------------------+
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
+─────────────────────────────────+             +───────────────────────────────────+
| CHILD TSG: Transatel demo       |             | CHILD TSG: tenant-1               |
| TSG ID: 1291887562              |             | TSG ID: 1632530514                |
| • Full SIM Inventory Management |             | • Scoped SIM Fleet & Groups       |
| • Dynamic 5G Group Assignments  |             | • Tenant-isolated Zero-Trust      |
| • Fast-Path Session Re-Anchor   |             | • Dedicated Interconnect CIDR     |
+─────────────────────────────────+             +───────────────────────────────────+
```

### 4.2 Permission Capabilities Matrix
* ✅ **Multi-Tenant Hierarchy Traversal**: Allows the portal to dynamically discover and switch between all child enterprise tenants (`/tenancy/v1/tenant_service_groups/{root_tsg}/operations/list_children`).
* ✅ **5G Subscriber Management**: Full programmatic control to list, create, update SIM metadata, and assign security policy groups across any child tenant.
* ✅ **Real-Time Session Telemetry & Fast-Path**: Instant UE session creation and policy flush via `/mt/manage/5g/ueSession/register`.
* ℹ️ **CIE DSS Core Sync Scope**: The dedicated `/sse/config/v1/ciedss` directory synchronization configuration API is an SCM core infrastructure endpoint that uses folder-scoped query parameters (`?folder=Shared` or tenant folder). The 5G Fast-Path session re-anchor provides the optimal instant synchronization mechanism for multi-tenant deployments.

---

## 5. Operational Workflow: MSSP vs Enterprise Customer

```
+-----------------------------------------------------------------------------------+
| MSSP (Transatel / Operator)                      ENTERPRISE CLIENT (SOC / IT)     |
+-----------------------------------------------------------------------------------+
| 1. Provisions Root Interconnect CIDR             1. Inspects SIM Fleet by Vertical|
|    (e.g. 10.56.0.192/27, 10.56.0.224/27)            (POS, AGVs, Scanners, iPads)  |
|                                                                                   |
| 2. Deploys Pre-Packaged Security Templates       2. Detects Anomalous IoT Device  |
|    (OT, PCI-DSS, Quarantine profiles)               in Monitoring Dashboard       |
|                                                                                   |
| 3. Delegates Child Tenant Access                 3. Shifts SIM to Quarantine Group|
|    via Scoped Service Account                        in 1-Click with Fast-Path    |
|                                                                                   |
| 4. Monitors Aggregate Global SASE Throughput     4. Threat is Neutralized in < 2s |
|    across all Enterprise Tenants                    without carrier SIM suspension|
+-----------------------------------------------------------------------------------+
```

---

## 6. Summary & Recommendations

1. **Keep the Seed SIM pattern active** for all critical quarantine and maintenance groups to ensure pre-compiled firewall readiness.
2. **Use the 5G Fast-Path mechanism** to provide sub-2-second policy shifts during live demonstrations and incident response workflows.
3. **Leverage the `Multitenant Superuser` delegation** to maintain seamless multi-tenant isolation across all enterprise customer service groups.
