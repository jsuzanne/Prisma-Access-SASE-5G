# 🎙️ Live Trade Show Demonstration Script (SIDO / MWC / IoT World)
## "Agentless Zero-Trust 5G Security & Dynamic Micro-Segmentation: IT vs. IoT"
**Target Audience**: CIO, CISO, VP Innovation, Heads of OT/IoT & Network Infrastructure.  
**Recommended Duration**: 3 to 5 minutes.

---

## 🧭 1. Executive Cheat Sheet & Access Matrix

| Security Access Matrix | 🌐 Public Internet (Web / SaaS) | 🏢 Private IT App (Datacenter) | 🏭 Web IoT App (Datacenter) |
| :--- | :---: | :---: | :---: |
| **📱 iPhone (IT Group)** | ✅ **ALLOWED** *(Inspected via SASE)* | ✅ **ALLOWED** *(Corporate Access)* | ❌ **BLOCKED** *(IoT Isolation)* |
| **📟 iPad (IoT Group)** | ❌ **BLOCKED** *(Anti-Exfiltration / C2)* | ❌ **BLOCKED** *(IT Cloaking)* | ✅ **ALLOWED** *(Telemetry / SCADA)* |
| **🚨 iPad (QUARANTINE Shift)** | ❌ **BLOCKED** | ❌ **BLOCKED** | ❌ **BLOCKED INSTANTLY (< 2s)** |

---

## 🖥️ 2. Stand Environment & The 4 Active Screens

1. **📱 iPhone (IT eSIM Profile)**: Connected over cellular 5G (APN `sasetest`).
2. **📟 iPad (IoT eSIM Profile)**: Connected over cellular 5G (APN `sasetest`).
3. **💻 Laptop Screen 1**: **Prisma SASE 5G Portal** (`http://localhost:8000`).
4. **💻 Laptop Screen 2**: **Strata Cloud Manager (SCM)** (`stratacloudmanager.paloaltonetworks.com`) under **Activity > Logs > Traffic**.

---

## 🎬 3. Step-by-Step Demonstration Sequence

```
[00:00] The 45-Second CIO Hook (The Agentless Dilemma in Cellular IoT)
   ↓
[00:45] STEP 1: Unified Fleet Visibility & Identity Anchoring (On Laptop)
   ↓
[01:30] STEP 2: The IT Employee Experience (On iPhone)
   ↓
[02:30] STEP 3: The Industrial IoT Persona (On iPad)
   ↓
[03:30] STEP 4: The Live Climax — Anomaly Detection & Fast-Path Quarantine (< 2s)
   ↓
[04:30] Executive Conclusion & ROI Takeaways for the CIO
```

---

### 🎙️ [00:00 - 00:45] The CIO Hook (Facing the visitor)

> **🗣️ What you say to the CIO:**  
> *"Hello! Today, your remote employees and your critical field devices (smart meters, industrial PLCs, connected vehicles, cameras) all connect over public 5G networks.  
> The major headache for every CISO and CIO: **you cannot install a software agent (like an EDR or GlobalProtect client) on an IoT sensor or a CCTV camera**.  
> Through our integration of **Palo Alto Networks Prisma SASE** with **Transatel 5G Core**, we enforce Zero-Trust security **natively at the cellular network core level**—100% agentless, transparent, and instant."*

---

### 💻 [00:45 - 01:30] STEP 1: Real-Time Fleet & Identity Correlation

* **Device**: Your Laptop — [Prisma SASE 5G Application](http://localhost:8000).
* **What you do**:
  1. Open the **SIM Inventory** tab.
  2. Highlight the iPhone eSIM mapped to the `IT-Corporate` group, and the iPad eSIM mapped to the `IoT-Sensors` group.
* **What you say:**  
  > *"Notice how the moment each eSIM attaches to the 5G network, our platform correlates the physical SIM hardware identity (IMSI/IMEI) with its IP lease and dynamic business security group. The Palo Alto Networks SASE firewall recognizes device identity and context before the very first packet leaves the cellular tower."*

---

### 📱 [01:30 - 02:30] STEP 2: The IT Persona (iPhone)

* **Device**: Hold the **iPhone**.
* **What you do**:
  1. Open Safari on the iPhone and navigate to `www.google.com` or `www.lemonde.fr` ➔ **Loads instantly.**
  2. Navigate to the internal **Private IT App** URL hosted in the Datacenter ➔ **Access granted (200 OK).**
  3. Navigate to the internal **Web IoT App** URL in the Datacenter ➔ **Connection Blocked / Timed Out.**
  4. *(Optional)* Switch to the Strata Cloud Manager screen on your laptop to display the green Allowed log for IT traffic and the red Deny log for the IoT destination.
* **What you say:**  
  > *"On this iPhone provisioned with the IT profile:  
  > 1. Internet browsing is fully allowed, inspected, and protected by Palo Alto Networks Next-Gen Security.  
  > 2. I have full access to internal IT datacenter management systems.  
  > 3. However, if I attempt to reach the sensitive IoT industrial control web portal, **I am instantly blocked**. IT users have zero business accessing raw IoT infrastructure."*

---

### 📟 [02:30 - 03:30] STEP 3: The IoT Persona (iPad)

* **Device**: Hold the **iPad**.
* **What you do**:
  1. Open Safari on the iPad and attempt to browse to `www.google.com` ➔ **Blocked immediately (Security block page / Connection reset).**
  2. Navigate to the internal **Private IT App** URL ➔ **Blocked immediately.**
  3. Navigate to the internal **Web IoT App** URL ➔ **IoT Telemetry Dashboard renders smoothly (OK).**
* **What you say:**  
  > *"Now let's pick up this iPad simulating a field PLC or an industrial terminal:  
  > 1. If an attacker breaches the device or malware attempts command-and-control (C2) callback or data exfiltration over the web, **it is physically impossible—public Internet is 100% cloaked**.  
  > 2. Access to internal corporate IT systems is strictly prohibited.  
  > 3. Only its designated datacenter application—the industrial telemetry server—is accessible."*

---

### ⚡ [03:30 - 04:30] STEP 4: The Live Climax — Threat Containment & Fast-Path Quarantine (< 2s)

* **Devices**: Your **Laptop (Prisma SASE 5G App)** then the **iPad**.
* **What you say before triggering:**  
  > *"Now, let's look at a critical zero-day scenario: your SOC detects suspicious network scanning from this IoT device. You need to isolate it immediately without sending a technician to the field and without waiting for background directory sync cycles."*

* **What you do:**
  1. **On your Laptop**: In SIM Inventory, click `Edit SIM` for the iPad, change its security group to **`Restrictive` / `Quarantine`**, and click **Save**.
  2. Click the **`⚡ Fast-Path Sync`** button in the top toolbar.
  3. In the confirmation modal, click **`[⚡ Execute Fast-Path Sync Now]`** ➔ Point out the real-time execution latency on screen: **`~250ms (Dataplane Re-anchored)`**.
  4. **Pick up the iPad immediately**: Refresh the Web IoT App page (which was working 5 seconds ago) ➔ **Instantly Blocked!**
  5. **On SCM (Laptop)**: Show the live red Deny security event tagged with the quarantined IMSI identity.

* **What you say:**  
  > *"In under 2 seconds, without touching the iPad, without rebooting the 5G modem, and bypassing the 45-minute directory polling delay, the security policy was flushed directly into the SASE Dataplane. The compromised asset is neutralized."*

---

### 🏆 [04:30 - 05:00] Executive Wrap-Up (The 3 Key CIO Value Pillars)

> **🗣️ What you say to conclude:**  
> *"To summarize the business value for your enterprise:  
> 1. **Agentless Zero-Touch**: Protect any cellular IoT device (from a $15 sensor to a heavy fleet vehicle) with zero software footprint on the endpoint.  
> 2. **Identity-Based Policy**: Policies are anchored to immutable 5G cryptographic hardware identities (SIM/eSIM), not ephemeral dynamic IPs.  
> 3. **Instant Incident Response**: Real-time (< 2s) quarantine capability to isolate compromised field assets before threats can spread laterally to your core datacenter."*

---

## 💡 4. Stand FAQ: Answers to the 3 Most Common CIO Questions

1. **"Do I need on-premise appliances or SD-WAN edge boxes at each remote site?"**  
   👉 *No hardware required on-premise. Cellular 5G traffic routes seamlessly from the carrier cell towers (Transatel/NTT) straight to cloud-native Prisma Access SASE POPs.*

2. **"How does this differ from a standard carrier Private APN?"**  
   👉 *A standard Private APN only performs basic, blind IP routing without threat inspection. Prisma SASE 5G delivers Next-Gen Firewall (NGFW) threat prevention, IPS, URL filtering, Zero-Trust micro-segmentation, and per-SIM user-ID correlation.*

3. **"Can this scale to tens of thousands of IoT devices globally?"**  
   👉 *Yes. The architecture is carrier-grade and multi-tenant, natively architected to orchestrate and secure global fleets spanning hundreds of thousands of cellular endpoints.*
