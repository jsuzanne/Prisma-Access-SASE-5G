# 🎙️ Script Scénario de Démonstration Stand (SIDO / Salons IoT & IT)
## « Sécurité Zero-Trust 5G & Segmentation sans Agent : IT vs IoT »
**Public cible** : DSI (CIO), RSSI (CISO), Directeurs de l'Innovation, Responsables Réseau & IoT.  
**Durée conseillée** : 3 à 5 minutes chrono.

---

## 🧭 1. Fiche Réflexe & Matrice des Flux

| Matrice des Accès | 🌐 Internet Public (Web/SaaS) | 🏢 App Privée IT (Datacenter) | 🏭 App Web IoT (Datacenter) |
| :--- | :---: | :---: | :---: |
| **📱 iPhone (Groupe IT)** | ✅ **AUTORISÉ** *(Sécurisé SASE)* | ✅ **AUTORISÉ** *(Accès Métier)* | ❌ **BLOQUÉ** *(Isolation IoT)* |
| **📟 iPad (Groupe IoT)** | ❌ **BLOQUÉ** *(Anti-Exfiltration)* | ❌ **BLOQUÉ** *(Cloisonnement IT)* | ✅ **AUTORISÉ** *(Télégestion)* |
| **🚨 iPad (Bascule QUARANTAINE)** | ❌ **BLOQUÉ** | ❌ **BLOQUÉ** | ❌ **BLOQUÉ IMMÉDIATEMENT (< 2s)** |

---

## 🖥️ 2. L'Environnement du Stand (Les 4 écrans en jeu)

1. **📱 iPhone (eSIM IT)** : Connecté en 5G cellulaire (APN `sasetest`).
2. **📟 iPad (eSIM IoT)** : Connecté en 5G cellulaire (APN `sasetest`).
3. **💻 Votre Laptop (Écran 1)** : Portail **Prisma SASE 5G** (`http://localhost:8000`).
4. **💻 Votre Laptop (Écran 2)** : Console **Strata Cloud Manager (SCM)** (`stratacloudmanager.paloaltonetworks.com`) sur l'onglet **Activity > Logs > Traffic**.

---

## 🎬 3. Déroulé Séquentiel Step-by-Step

```
[00:00] Accroche & Problématique Métier
   ↓
[00:45] STEP 1 : Présentation de l'inventaire unifié (Sur le PC)
   ↓
[01:30] STEP 2 : Démonstration du profil IT (Sur l'iPhone)
   ↓
[02:30] STEP 3 : Démonstration du profil IoT (Sur l'iPad)
   ↓
[03:30] STEP 4 : Le Coup d'Éclat — Alerte & Quarantaine Fast-Path (< 2s)
   ↓
[04:30] Conclusion & ROI pour le DSI
```

---

### 🎙️ [00:00 - 00:45] L'Accroche CIO / DSI (Face au visiteur)

> **🗣️ Ce que vous dites au CIO :**  
> *"Bonjour ! Aujourd'hui, vos collaborateurs et vos équipements industriels (capteurs, automates, passerelles 5G) se connectent tous en cellulaire.  
> Le casse-tête pour un DSI : **il est impossible d'installer un agent de sécurité (comme GlobalProtect ou un EDR) sur des capteurs IoT ou des caméras**.  
> Avec l'intégration **Palo Alto Networks Prisma SASE** et le coeur de réseau **5G Transatel**, nous appliquons le Zero-Trust **directement au niveau du réseau cellulaire**, de façon 100% transparente et sans aucun agent."*

---

### 💻 [00:45 - 01:30] STEP 1 : Montrer la Flotte & la Corrélation d'Identité

* **Support** : Votre Laptop — [Application Prisma SASE 5G](http://localhost:8000).
* **Ce que vous faites** :
  1. Ouvrez l'onglet **SIM Inventory**.
  2. Pointez l'eSIM de l'iPhone dans le groupe `IT-Corporate` et l'eSIM de l'iPad dans le groupe `IoT-Sensors`.
* **Ce que vous dites :**  
  > *"Regardez : dès que les eSIM s'attachent à la 5G, notre portail corrèle l'identifiant matériel de la SIM (l'IMSI/IMEI) avec son adresse IP et son groupe de politique métier. Le firewall Prisma Access connaît instantanément l'identité de chaque objet avant même qu'un seul paquet ne parte."*

---

### 📱 [01:30 - 02:30] STEP 2 : Le Device IT (iPhone)

* **Support** : L'**iPhone** en main.
* **Ce que vous faites** :
  1. Ouvrez Safari sur l'iPhone et allez sur `www.google.com` ou `www.lemonde.fr` ➔ **La page s'ouvre rapidement.**
  2. Ouvrez l'URL de l'**App Privée IT** du Datacenter ➔ **Accès validé (OK).**
  3. Ouvrez l'URL de l'**App Web IoT** du Datacenter ➔ **Page de blocage / Timeout.**
  4. *(Optionnel)* Basculez sur l'écran SCM (Laptop) pour montrer le log vert sur le trafic IT et le log rouge de deny vers l'App IoT.
* **Ce que vous dites :**  
  > *"Sur cet iPhone avec le profil IT :  
  > 1. J'accède à Internet de manière entièrement inspectée par la sécurité Palo Alto Networks.  
  > 2. J'accède aux applications internes du Datacenter réservées aux équipes IT.  
  > 3. En revanche, si j'essaie d'aller sur l'application de contrôle des automates IoT du Datacenter, **je suis immédiatement bloqué**. L'IT n'a rien à faire sur les réseaux sensibles de l'IoT."*

---

### 📟 [02:30 - 03:30] STEP 3 : Le Device IoT (iPad)

* **Support** : L'**iPad** en main.
* **Ce que vous faites** :
  1. Ouvrez Safari sur l'iPad et essayez d'aller sur `www.lemonde.fr` ou `www.google.com` ➔ **Bloqué immédiatement (Security Block Page ou connexion refusée).**
  2. Ouvrez l'URL de l'**App Privée IT** du Datacenter ➔ **Bloqué immédiatement.**
  3. Ouvrez l'URL de l'**App Web IoT** du Datacenter ➔ **Le tableau de bord IoT s'affiche parfaitement (OK).**
* **Ce que vous dites :**  
  > *"Prenons maintenant cet iPad qui simule un automate ou une tablette industrielle IoT :  
  > 1. Si un attaquant prend le contrôle de l'objet ou qu'un malware tente d'exfiltrer des données sur Internet, **c'est impossible, Internet est 100% hermétique**.  
  > 2. L'accès aux serveurs de gestion IT du siège est également refusé.  
  > 3. En revanche, sa seule destination autorisée — son serveur de collecte IoT dans le Datacenter — fonctionne parfaitement."*

---

### ⚡ [03:30 - 04:30] STEP 4 : Le Coup d'Éclat — Incident & Quarantaine Fast-Path (< 2s)

* **Support** : Votre **Laptop (App 5G)** puis l'**iPad**.
* **Ce que vous dites avant d'agir :**  
  > *"Maintenant, scénario catastrophe : votre SOC détecte qu'un automate IoT est compromis ou présente un comportement suspect. Vous devez l'isoler immédiatement sans attendre et sans envoyer un technicien sur site."*

* **Ce que vous faites :**
  1. **Sur votre App (Laptop)** : Allez sur l'inventaire SIM, cliquez sur l'eSIM de l'iPad (`Edit SIM`), changez son groupe vers **`Restrictive` / `Quarantine`**, et cliquez sur **Save**.
  2. Cliquez sur le bouton **`⚡ Fast-Path Sync`** en haut à droite.
  3. Dans le modal, cliquez sur **`[⚡ Execute Fast-Path Sync Now]`** ➔ Montrez le temps de réponse à l'écran : **`~250ms (Dataplane Re-anchored)`**.
  4. **Reprenez l'iPad immédiatement** : Actualisez la page de l'App Web IoT (qui fonctionnait il y a 5 secondes) ➔ **Blocage instantané !**
  5. **Sur le Laptop (SCM)** : Montrez le log rouge en direct avec la règle de sécurité Quarantine appliquée à l'IMSI de l'iPad.

* **Ce que vous dites :**  
  > *"En moins de 2 secondes, sans toucher à l'iPad, sans redémarrer le modem 5G et sans attendre les 45 minutes habituelles de synchronisation d'annuaire, la politique de sécurité a été poussée directement dans le Dataplane SASE. L'équipement est neutralisé."*

---

### 🏆 [04:30 - 05:00] Conclusion & Pitch de Clôture (Les 3 bénéfices DSI)

> **🗣️ Ce que vous dites pour conclure :**  
> *"En résumé, pour votre entreprise, Prisma SASE 5G c'est :  
> 1. **Zero-Touch / Agentless** : Vous protégez n'importe quel objet 5G (du capteur à 10€ jusqu'au véhicule connecté).  
> 2. **Visibilité & Contrôle applicatif** : Vos politiques de sécurité s'appliquent sur des identités 5G (eSIM) et non plus sur des IP volatiles.  
> 3. **Isolation immédiate** : Une réactivité temps réel pour couper un équipement compromis avant qu'une attaque ne se propage au Datacenter."*

---

## 💡 4. Anti-Sèche : Réponses aux 3 Questions Fréquentes du CIO

1. **"Est-ce que ça nécessite une passerelle ou une box supplémentaire sur site ?"**  
   👉 *Non, aucune appliance sur site. Le trafic 5G passe directement de l'antenne opérateur (Transatel/NTT) aux points de présence Prisma Access dans le Cloud.*

2. **"Quelle est la différence avec un APN privé classique ?"**  
   👉 *Un APN privé classique fait juste du routage IP aveugle. Ici, vous bénéficiez du firewall applicatif de nouvelle génération (NGFW), de l'inspection antivirale, de l'IPS, de la segmentation Zero-Trust et de la corrélation d'identité par SIM.*

3. **"Combien de SIMs peut-on gérer ?"**  
   👉 *L'architecture est nativement multitenant et conçue pour des flottes industrielles de plusieurs dizaines de milliers d'objets connectés à l'échelle mondiale.*
