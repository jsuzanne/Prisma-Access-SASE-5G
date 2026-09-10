# Changelog

All notable changes to **Prisma SASE 5G Manager** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-09-11

### Added
- **SIDO 2026 5G IoT Industry Presets & Auto-Enrichment**:
  - Added 7 industry verticals: *Smart City & Utilities*, *Industrial IoT & Robotics*, *Connected Healthcare*, *Logistics & Fleet Tracking*, *Retail & Smart POS*, *Agritech & Environmental*, and *Energy & Smart Grid*.
  - **Auto-Enrich Fleet** feature to automatically assign industry device profiles to existing SIMs in SCM inventory without creating duplicates.
  - Realistic Transatel NTT IMSI generator (`generate_transatel_imsi`) and Luhn-compliant IMEI generator (`generate_valid_imei`).
  - Dual SIM table view switch (*Industry Fleet View* vs. *Raw SCM View*).
  - Clear, high-contrast typography in the SIM table optimized for small and large screens.
- **English Localization**:
  - Full English translation across all UI components, modals, CLI prompts, and API response messages.
- **Unit Test Suite**:
  - Added `tests/test_presets_and_metadata.py` validating preset integrity, Luhn algorithms, and metadata correlation.

---

## [1.3.0] - 2026-09-10

### Added
- **Persistent Configuration Storage**:
  - Added persistent configuration directory (`config/config.json`) and Docker volume mount support.
  - Optional `.env` file support for 1-click zero-config installations.
- **Active 5G Sessions Alignment**:
  - Aligned 3 live active SIM sessions with SCM telemetry.
  - Cache invalidation and instant refresh button for SIM inventory with spinning animations.

### Fixed
- Protected client secret and credentials handling across frontend and backend.
- Made 5G Summary refresh button explicitly invalidate server cache.

---

## [1.2.0] - 2026-09-10

### Added
- **Display & Typography Scaling**:
  - Dynamic font size scaling controls (*Standard 100%*, *Comfortable 115%*, *Large 130%*) for 2K/4K high-resolution monitors and presentation displays.
- **MSSP & Carrier Co-Branding**:
  - Top header co-branding for Transatel (NTT) and Aeris Communications with custom branding presets.
- **Strata Cloud Manager (SCM) 11-Column UE Mappings Table**:
  - Replicated exact SCM portal layout with dynamic SIM IP allocation and active status correlation.
- **Branding Assets**:
  - Modern SVG, PNG, and ICO favicons with PANW Flame and 5G Core styling.

### Fixed
- Fixed UE mappings rendering error and added interactive tenant switcher dropdown in the active hierarchy banner.
- Resolved header responsiveness issues to keep all right-side status indicators permanently visible without horizontal scrolling.

---

## [1.1.0] - 2026-09-10

### Added
- **Live API Inspector & Debug Console**:
  - Real-time logging of HTTP request/response payloads with 1-click cURL clipboard copy.
- **5G Identity Groups Management**:
  - SCM-aligned SIM Group assignment and dynamic group creation/deletion.
  - Protected built-in system groups (`Restrictive` and `Permissive`).
- **5G SASE Summary Dashboard**:
  - Real-time throughput trend charts, connected device breakdown, and active alerts overview.

### Fixed
- Resolved SCM 400 validation by requiring and auto-assigning initial SIM identities when creating 5G groups.
- Added credential fallback in `/api/config/test` when secret is left empty.

---

## [1.0.0] - 2026-09-09

### Added
- **Initial Release of Prisma SASE 5G Toolkit**:
  - Complete Python SDK client for Palo Alto Networks Strata Cloud Manager (SCM) 5G UE APIs.
  - CLI management tool (`manage_5g.py`) with lifecycle test automation (`test_lifecycle.py`).
  - FastAPI asynchronous web server (`app.py`) with interactive UI.
  - CI/CD automated pipeline via GitHub Actions (`.github/workflows/ci.yml`) publishing multi-architecture Docker images (`linux/amd64`, `linux/arm64`) to Docker Hub (`jsuzanne/prisma-5g-sase:latest`).
