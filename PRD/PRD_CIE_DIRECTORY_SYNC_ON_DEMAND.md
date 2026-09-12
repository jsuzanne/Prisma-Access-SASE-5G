# PRD: On-Demand Cloud Identity Engine (CIE) & 5G Subscriber Policy Sync

- **Document ID**: `PRD-5G-CIE-SYNC-001`
- **Feature Name**: On-Demand Cloud Identity Engine (CIE) & 5G Policy Push Engine
- **Target Audience**: Field Solution Architects, Demo Engineers, SASE Product Teams
- **Status**: `PROPOSED / READY FOR REVIEW`
- **Version**: `1.0.0`
- **Date**: `2026-09-12`

---

## 1. Executive Summary & Problem Statement

### 1.1 Context
In **Palo Alto Networks Prisma SASE 5G** integrated with **Telecom / 5G Core networks** (e.g. Transatel NTT, Tier-1 MNOs, Private 5G), User Equipment (SIM / UE) identities are mapped to Zero-Trust Subscriber Security Policy Groups (e.g., *VIP-Sensors*, *Default-Permissive*, *Threat-Quarantine-Restrictive*).

### 1.2 The 40-Minute Propagation Challenge
Under default Strata Cloud Manager (SCM) and Cloud Identity Engine (CIE) operations:
* **Background Polling Cycle**: The Cloud Identity Engine Directory Sync Service (CIE DSS) and the security policy enforcement dataplane (Security Processing Nodes / SPNs) refresh directory group caches on an asynchronous schedule (typically **30 to 45 minutes**).
* **Impact on Live Demonstrations (Trade Shows / Customer PoCs)**:
  * When demonstrating a live security group shift (e.g. moving a compromised 5G IoT camera from *Permissive Group* to *Quarantined/Restrictive Group* to block lateral movement), waiting up to 40 minutes for the policy to take effect breaks the demonstration narrative.
  * Trade show environments (e.g. SIDO Lyon, Mobile World Congress) require **instant, sub-5-second policy enforcement verification**.

---

## 2. Technical Architecture & Investigation Findings

### 2.1 Cloud Identity Engine Directory Sync Service (CIE DSS) API Overview
According to the official Palo Alto Networks documentation ([pan.dev SCM CIE DSS API](https://pan.dev/scm/api/config/ciedss/ciedss/)):
* **Endpoint Family**: `/sse/config/v1/ciedss` and `/config/deployment/v1.0/jobs`
* **Purpose**: Manages Cloud Identity Engine directory instances, attributes, agent synchronization, and candidate configuration push jobs.
* **IAM Scope & Permissions**:
  * The default 5G Management service account (`5G Management Service`) has access to `/mt/manage/5g/...` and `/tenancy/v1/...`.
  * Triggering full SCM CIE DSS configuration push jobs requires the `Strata Cloud Manager Configuration Administrator` or `Identity Administrator` role on the Service Account.

### 2.2 The Two-Tier Propagation Architecture

To achieve instant demo responsiveness while remaining fully aligned with enterprise SCM workflows, the solution implements a **Two-Tier Synchronization Model**:

```
+-----------------------------------------------------------------------------------+
|                            PRISMA SASE 5G DEMO PORTAL                             |
|                                                                                   |
|  [⚡ Sync Policies Now (Push to Dataplane)] Button (On-Demand User Action)         |
+----------------------------------------+------------------------------------------+
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
   +-----------------------+                           +-----------------------+
   |   TIER 1: SCM LEVEL   |                           |   TIER 2: 5G LEVEL    |
   |   (CIE DSS Sync API)  |                           |  (Fast-Path Session)  |
   +-----------------------+                           +-----------------------+
   | - Trigger SCM Push    |                           | - Cycle UE Session    |
   | - Candidate commit    |                           | - Re-evaluate IP/IMSI |
   | - Background async    |                           | - Instant DP flush    |
   | - Enterprise record   |                           | - < 2s live reaction  |
   +-----------------------+                           +-----------------------+
               |                                                   |
               +-------------------------+-------------------------+
                                         |
                                         v
               +---------------------------------------------------+
               |     PRISMA SASE SECURITY ENFORCEMENT DATAPLANE    |
               |                                                   |
               |    Immediate Zero-Trust Policy Block / Allow       |
               +---------------------------------------------------+
```

#### Tier 1: SCM CIE DSS Sync & Candidate Push (Global Backend)
* Triggers an on-demand synchronization job in Strata Cloud Manager to persist the updated identity mapping into the Cloud Identity Engine.
* Checks job status asynchronously via `/config/deployment/v1.0/jobs` or `/sse/config/v1/jobs`.

#### Tier 2: 5G Fast-Path Session Context Re-Anchoring (Instant Dataplane Flush)
* When a SIM's group is shifted in the demo, the 5G Management engine executes a micro-cycle of the UE session context (`/mt/manage/5g/ueSession/register` with active IMSI + IP allocation).
* **Result**: The UPF/SPN enforcement layer immediately clears its cached session group association and re-evaluates the subscriber policy against the new group membership in **< 2 seconds**.

---

## 3. Detailed Functional Specifications

### 3.1 User Experience (UI/UX) Requirements

#### 1. Header & Groups View Sync Controls
* **Primary Sync Button**: Located in the top subheader and inside the *Groups & Policies* tab:
  * Label: `[⚡ Sync 5G Policies Now]`
  * Tooltip: *"Push candidate subscriber group changes directly to the 5G dataplane and trigger CIE sync."*
  * Visual feedback: Pulsing sync icon during execution with live progress spinner.

#### 2. Synchronize Confirmation & Progress Modal
* When clicked, a modal or toast displays the 3-step synchronization sequence:
  1. `[Step 1]` Committing subscriber policy group updates to SCM (`/mt/manage/5g/userGroup/...`).
  2. `[Step 2]` Re-anchoring active 5G UE session contexts to force instant dataplane flush.
  3. `[Step 3]` Triggering Cloud Identity Engine (CIE DSS) backend consistency synchronization.
* **Duration**: Total execution completes in under 3 seconds.

#### 3. Real-Time Status & Last Sync Indicator
* Displays a compact badge: `Last Dataplane Sync: Just now (09:42:15)` in the Groups & Policies card.

---

### 3.2 Backend API Specifications (Planned)

#### Endpoint 1: `POST /api/cie/sync`
* **Description**: Triggers the two-tier policy synchronization on-demand.
* **Request Body**:
  ```json
  {
    "tsg_id": "1965438697",
    "mode": "hybrid", 
    "target_identities": ["901370001420683", "901370007299137"],
    "force_session_refresh": true
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "success": true,
    "sync_id": "sync-7610197f-5be0",
    "timestamp": 1726134140,
    "fast_path_sessions_updated": 2,
    "cie_sync_status": "triggered_or_fastpath",
    "message": "Subscriber policy groups successfully synchronized to 5G dataplane in 1.42s"
  }
  ```

#### Endpoint 2: `POST /api/groups/shift-policy`
* **Description**: High-level atomic endpoint for demos that shifts a SIM from Group A to Group B and triggers instant synchronization in a single API call.
* **Request Body**:
  ```json
  {
    "imsi": "901370001420683",
    "target_group_id": "6000000002",
    "target_group_name": "Restrictive-Quarantine",
    "auto_sync": true
  }
  ```

---

## 4. Security, Credentials & Zero-Trust Governance

1. **No Credentials in Version Control**:
   * All API keys, Client IDs, and Client Secrets must remain strictly managed via `.env` / `config/config.json`.
   * No service account tokens, client secrets, or live TSG IDs will ever be stored in the PRD or public GitHub repositories.
2. **Permission Fallback Gracefully**:
   * If the active Service Account does not possess full SCM Configuration Admin privileges (e.g. returns `403 Access Denied` on `/sse/config/v1/ciedss`), the engine automatically falls back to the **5G Fast-Path Session Re-Anchoring**, ensuring the demo remains 100% operational without failing.
3. **Audit Logging**:
   * Every on-demand policy push is logged to the in-memory **API Debugger & Inspector** (`#modal-api-debugger`) with full request/response timestamps and status codes.

---

## 5. Rollout Plan & Milestones

| Phase | Milestone Description | Target Timeline | Status |
|---|---|---|---|
| **Phase 1** | Architectural Study & API Endpoint Connectivity Probe | 2026-09-12 | **COMPLETED** |
| **Phase 2** | PRD Specification & Technical Architecture Documentation | 2026-09-12 | **COMPLETED** |
| **Phase 3** | Backend `src/cie_sync.py` Engine & Fast-Path Implementation | Future Release | Planned |
| **Phase 4** | Frontend `[⚡ Sync 5G Policies Now]` Button & Interactive Modal | Future Release | Planned |
| **Phase 5** | End-to-End Validation with Live SASE Security Traffic Blocker | Future Release | Planned |

---

## 6. Review & Sign-Off

- **Lead Architect**: Jean-Louis SUZANNE
- **Repository**: [github.com/jsuzanne/Prisma-SASE-5G](https://github.com/jsuzanne/Prisma-SASE-5G)
- **Document Path**: `PRD/PRD_CIE_DIRECTORY_SYNC_ON_DEMAND.md`
