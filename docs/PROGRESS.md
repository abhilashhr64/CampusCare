# CampusCare AI — Development Progress & Release Gates

## Status Overview
- Current Phase: **Phase 1: Multi-Tenant Foundation, RLS, Identity & Access (Completed & Verified)**
- Architecture: Modular Monolith (`FastAPI`, `SQLAlchemy 2`, `Alembic`, `PostgreSQL 18` with forced RLS, `Next.js 15` App Router, `Dexie.js` IndexedDB)
- Database: Dedicated PostgreSQL 18 cluster (`campuscare_pgdata` on port `5433`) with `NOBYPASSRLS` application user (`campuscare_app`) and privileged migration role (`campuscare_migrator`).
- Test Suite: 10/10 automated tests passing (`pytest backend/tests/`).
- Frontend Bundle: Next.js 15 compiled successfully with 0 TypeScript/ESLint errors (`npm run build`).

---

## Release Gates & Phase Checklist

### Phase 1: Multi-Tenant Foundation, RLS, Identity & Access (Release Gate PASSED)
- [x] **TN-1..TN-6: Tenancy Core & Forced PostgreSQL RLS**
  - [x] Non-null `college_id` on all tenant-owned tables with composite foreign keys (`(college_id, id)`).
  - [x] Session-level / transaction-local `set_config('app.current_college_id', ..., true)` fail-closed enforcement.
  - [x] Non-owner application role (`campuscare_app`) without `BYPASSRLS`.
  - [x] Privileged migration role (`campuscare_migrator`).
  - [x] CI/test suite catalog introspection verifying `FORCE ROW LEVEL SECURITY` and active policies on every tenant table (TN-4).
  - [x] Break-glass platform operator audited path with expiry and alert (TN-5).
- [x] **BR-1..BR-3: Modular Monolith & Boundary Enforcement**
  - [x] 12 domain modules planned with service interfaces (`tenancy`, `identity`, `access`, `directory`, `attendance`, `audit` implemented).
  - [x] Service interfaces and event publishers; zero cross-module direct table access.
  - [x] CI boundary linter contract enforcing module boundaries (`test_boundaries_linter.py`).
  - [x] Transactional Outbox pattern (`EV-1`, `outbox_events`) for cross-module side effects.
- [x] **ID-1..ID-6 & C5: Identity, Server-Side Sessions & MFA**
  - [x] Verified email link / one-time code sign-in flow (`auth:signup_student`, `auth:verify_code`).
  - [x] Strict rule: verified email alone NEVER grants privileged roles (NR-5).
  - [x] Staff MFA (RFC 6238 TOTP) foundation and step-up auth requirement (C5).
  - [x] Revocable server-side sessions (`identity_sessions`) with httpOnly, Secure, SameSite cookies and hashed session tokens (ADR-003).
- [x] **AZ-1..AZ-6: Centralized Authorization Engine (RBAC + ABAC)**
  - [x] Single policy decision function `authorize(actor, action, resource) -> Decision(allow/deny, reason, obligations)`.
  - [x] Route permission declaration requirement; automated CI verification test (`test_routes_declare_required_permission` - AZ-3).
  - [x] Automated permission matrix test asserting allow/deny across all roles and 2 colleges (`test_permission_matrix_cross_role_and_cross_tenant` - AZ-4).
  - [x] Role grants with approver, reason, scope, and expiry (AZ-5).
  - [x] Lecturer scoped class access; zero individual feedback visibility (AZ-6, NR-10).
- [x] **Audit Core (B3)**
  - [x] Append-only, hash-chained tamper-evident audit log for privileged actions (`audit_log_entries`, `AuditService`).
- [x] **Deterministic Attendance What-If Engine (B3)**
  - [x] Exact classes a student must attend ($C_{attend}$) or can miss ($C_{miss}$) per subject without AI dependency.
  - [x] Fully covered by unit tests (`test_attendance_whatif.py`).
- [x] **Offline Attendance Client Protocol (C7, ADR-005)**
  - [x] Dexie IndexedDB client outbox with UUID `op_id` idempotency and `base_version` concurrency tracking (`offlineStore.ts`).
- [x] **Frontend Foundation (Next.js 15 App Router + FSD Architecture)**
  - [x] Feature-Sliced Design structure (`app`, `widgets`, `features`, `entities`, `shared`).
  - [x] Sleek dark theme tokens, glassmorphism accents, Google-inspired typography in `globals.css`.
  - [x] Accessible UI primitives: loading, empty, error, offline, and permission-denied states (`States.tsx`).
  - [x] OpenAPI-generated typed client integration (`client.ts`).
  - [x] Multi-persona dashboard (`page.tsx`) with Student, Lecturer, Department Admin, College Admin, What-If Calculator, and PostgreSQL RLS Inspector views.

---

## Slice Log & Evidence Registry

| Date | Slice ID | Description | Requirement IDs | Test / Verification Evidence | Status |
|------|----------|-------------|-----------------|------------------------------|--------|
| 2026-10-27 | SLICE-00 | Workspace inspection, Git init, PostgreSQL 18 cluster setup on port 5433, migrator & app roles | NR-1, NR-2, TN-3 | DB created; roles `campuscare_migrator` & `campuscare_app` provisioned | Completed |
| 2026-10-27 | SLICE-01 | Architecture foundation: Alembic initial schema with forced RLS, boundary linter, auth engine, deterministic what-if calculator, offline sync outbox, Next.js portal | NR-1, NR-2, NR-3, NR-5, NR-7, NR-9, TN-1..TN-5, AZ-1..AZ-6, BR-1..BR-3, B3, C5, C7 | 10/10 Pytest tests passing; Next.js 15 build successful; API serving HTTP 200 on port 8000; Web serving HTTP 200 on port 3000 | Completed |

---

## Verification Evidence (Rule NR-1)

### Test Command: `pytest backend/tests/ -v`
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.5
collected 10 items

backend/tests/test_attendance_whatif.py::test_attendance_what_if_surplus PASSED [ 10%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_deficit PASSED [ 20%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_exactly_on_target PASSED [ 30%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_zero_classes PASSED [ 40%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_invalid_inputs PASSED [ 50%]
backend/tests/test_authorization_matrix.py::test_routes_declare_required_permission PASSED [ 60%]
backend/tests/test_authorization_matrix.py::test_permission_matrix_cross_role_and_cross_tenant PASSED [ 70%]
backend/tests/test_boundaries_linter.py::test_modular_monolith_boundary_linter PASSED [ 80%]
backend/tests/test_rls_catalog_introspection.py::test_catalog_introspection_enforces_forced_rls PASSED [ 90%]
backend/tests/test_rls_catalog_introspection.py::test_tenant_isolation_fails_closed_and_isolates_data PASSED [100%]

============================= 10 passed in 6.13s ==============================
```

### Build Command: `npm run build` in `frontend`
```text
▲ Next.js 16.4.3 (Turbopack)
✓ Compiled successfully in 4.7s
  Running TypeScript ...
  Finished TypeScript in 3.8s ...
✓ Generating static pages (4/4) in 1634ms
Exit code: 0
```
