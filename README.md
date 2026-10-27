# CampusCare AI

CampusCare AI is a production-oriented, multi-tenant college services platform built as a secure modular monolith with verified identity, role-approved staff, complaint SLA countdowns, offline-first attendance, anonymous teacher feedback, and deterministic analytics.

---

## Architecture Highlights
- **PostgreSQL 18 with Forced Row-Level Security (`FORCE ROW LEVEL SECURITY`)**:
  - Runtime application connects using a non-owner role (`campuscare_app`) configured with `NOBYPASSRLS` (**NR-2**, **TN-3**).
  - All tenant tables include non-nullable `college_id` with composite foreign keys (**TN-1**).
  - Transactions dynamically set context via `set_config('app.current_college_id', ..., true)` (**TN-2**).
  - CI catalog introspection verifies forced RLS across all tenant tables (**TN-4**).
- **Modular Monolith & Architectural Boundary Enforcement**:
  - 12 domain modules communicating strictly through service interfaces and domain events (**BR-1**).
  - Automated CI boundary linter failing builds upon direct cross-module model imports (**BR-2**).
  - Atomic Transactional Outbox pattern (**EV-1**, **BR-3**).
- **Centralized Authorization Engine (RBAC + ABAC)**:
  - Single decision function `authorize(actor, action, resource) -> Decision` (**AZ-1**, **AZ-2**).
  - Deny-by-default; hiding UI buttons is purely cosmetic (**NR-3**).
  - Verified email alone never grants elevated privileges (**NR-5**).
  - Route permission declarations enforced by automated CI inspection (**AZ-3**, **AZ-4**).
- **Deterministic Attendance What-If Engine**:
  - Deterministic calculation of exact classes a student can miss ($C_{miss}$) or must attend ($C_{attend}$) per subject (**B3**).
- **Offline Attendance Protocol**:
  - IndexedDB client outbox (Dexie.js) with UUID `op_id` idempotency and `base_version` conflict detection (**C7**).
- **Tamper-Evident Audit Ledger**:
  - Append-only cryptographic hash-chained audit ledger ($SHA256(prev\_hash + actor + payload + timestamp)$) (**B3**).

---

## Project Structure
```
CAMPUSCARE-AI/
├── backend/
│   ├── src/
│   │   ├── core/         # Config, Database, Forced RLS, Security, Outbox, Boundaries
│   │   ├── modules/      # Tenancy, Identity, Access, Directory, Attendance, Audit
│   │   ├── api/          # Routers and dependencies
│   │   └── main.py       # FastAPI application
│   ├── alembic/          # Version-controlled migrations with RLS policies
│   └── tests/            # Automated test suite (RLS, Boundaries, Auth Matrix, What-If)
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js 15 App Router pages and layout
│   │   ├── features/     # Attendance What-If, Offline Store (Dexie)
│   │   ├── shared/       # OpenAPI client, UI state components, QueryProvider
│   └── package.json
└── docs/
    ├── MASTER_PROMPT.md  # Master development contract
    ├── PROGRESS.md       # Release gates & execution progress
    ├── ASSUMPTIONS.md    # Architectural choices & defaults
    ├── DEPENDENCIES.md   # Pinned dependencies & justifications
    └── adr/              # Architecture Decision Records (001 - 005)
```

---

## Quickstart Guide

### 1. Backend & Database Setup
```powershell
# Copy environment configuration
cp .env.example .env

# Run Alembic migrations
cd backend
.\.venv\Scripts\alembic upgrade head

# Run backend tests (10/10 automated tests)
.\.venv\Scripts\pytest tests/ -v

# Start FastAPI server (Port 8000)
.\.venv\Scripts\uvicorn src.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup
```powershell
cd frontend

# Install dependencies (pinned in package.json)
npm install

# Run production build
npm run build

# Start Next.js development server (Port 3000)
npm run dev
```

### 3. Open Portal
Navigate to [http://localhost:3000](http://localhost:3000) to access the interactive multi-persona portal.
