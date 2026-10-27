# CampusCare AI — Development Progress & Release Gates

## Status Overview
- Current Phase: **Phase 3: Campus AI (Knowledge Base, Citation-Grounded Assistant, Confirmed Drafts) (Completed & Verified)**
- Architecture: Modular Monolith (`FastAPI`, `SQLAlchemy 2`, `Alembic`, `PostgreSQL 18` with forced RLS, `Next.js 16` App Router, `Dexie.js` IndexedDB)
- Database: Dedicated PostgreSQL 18 cluster (`campuscare_pgdata` on port `5433`) with `NOBYPASSRLS` application user (`campuscare_app`) and privileged migration role (`campuscare_migrator`).
- Test Suite: **18/18 automated tests passing** (`pytest backend/tests/`).
- Frontend Bundle: Next.js 16 compiled successfully with 0 TypeScript/ESLint errors (`npm run build`).

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
- [x] **Frontend Foundation (Next.js App Router + FSD Architecture)**
  - [x] Feature-Sliced Design structure (`app`, `widgets`, `features`, `entities`, `shared`).
  - [x] Sleek dark theme tokens, glassmorphism accents, Google-inspired typography in `globals.css`.
  - [x] Accessible UI primitives: loading, empty, error, offline, and permission-denied states (`States.tsx`).
  - [x] OpenAPI-generated typed client integration (`client.ts`).
  - [x] Multi-persona dashboard (`page.tsx`) with Student, Lecturer, Department Admin, College Admin, What-If Calculator, and PostgreSQL RLS Inspector views.

---

### Phase 2: Reliable Workflows (Complaints, Anonymous Feedback, Attendance Sync & Worker) (Release Gate PASSED)
- [x] **Complaints & Grievances Workflows (B3 Signature Capability)**
  - [x] Committed SLA clocks and countdown timers based on category (`sla_committed_hours`, `sla_deadline`).
  - [x] Location-tagged grievance reporting with QR code tags (`location_tag`).
  - [x] Sensitive grievance flagging and role-scoped access control (`is_sensitive`).
  - [x] Closed-loop resolution confirmation: student verification and rating required before status moves to `CLOSED`.
  - [x] Reopen capability if resolution is rejected by the reporting student.
  - [x] Cryptographic tamper-evident hash chaining on audit ledger for all complaint lifecycle transitions.
  - [x] Unit and integration tests passing (`test_complaints_workflows.py`).
- [x] **Anonymous Teacher Feedback (NR-10 & ADR-004)**
  - [x] Physical unlinkability by design: decoupled `feedback_participations` (voter prevention) and `feedback_answers` (unlinked ratings).
  - [x] Zero student ID column, zero user reference, zero foreign key in answers table.
  - [x] Wide 4-hour epoch buckets (`YYYY-MM-DD-B...`) to thwart millisecond timestamp correlation attacks.
  - [x] $k \ge 5$ k-anonymity gate: individual or sparse feedback below threshold is completely hidden (`AZ-6`).
  - [x] Unit and integration tests passing (`test_feedback_anonymity.py`).
- [x] **Offline Attendance Synchronization Protocol (C7 & ADR-005)**
  - [x] Batch synchronization endpoint (`/attendance/sync-batch`).
  - [x] Client outbox idempotency key via UUID `op_id`.
  - [x] Optimistic concurrency conflict detection (`session.version > entry.base_version`).
  - [x] Server returns both server and client records on conflict without silent overwrite.
  - [x] Tamper-evident hash-chained audit logging for all attendance sessions (`ATTENDANCE_MARKED`).
  - [x] Unit and integration tests passing (`test_offline_attendance_sync.py`).
- [x] **Transactional Outbox Consumer & Dead-Letter Queue (EV-1..EV-3)**
  - [x] Atomic outbox event enqueueing within domain transactions (`publish_event`).
  - [x] Background worker batch consumer (`process_outbox_batch`, `run_worker_loop`).
  - [x] Automatic retry count tracking and exponential backoff handling.
  - [x] Poison message routing to `DEAD_LETTER` after 5 failed attempts (`EV-2`).
  - [x] Unit and integration tests passing (`test_outbox_worker.py`).
- [x] **Phase 2 Database Schema & Forced RLS (NR-9 & TN-1..TN-4)**
  - [x] Migration `8c4921513315_create_phase2_core_workflows.py` applied with `FORCE ROW LEVEL SECURITY` across all 7 new tenant tables.
  - [x] Tested upgrade, downgrade, and re-upgrade cleanly.

---

### Phase 3: Campus AI — Institutional Knowledge & Citation-Grounded Assistant (Release Gate PASSED)
- [x] **Institutional Knowledge Base (`knowledge`) (Rule TN-6, B2)**
  - [x] Document registration and chunk ingestion with composite foreign keys `(college_id, document_id)` under forced RLS.
  - [x] Strict tenant isolation: college chunks isolated to tenant, zero cross-tenant retrieval leaks (`test_knowledge_ingestion_and_cross_tenant_grounding_isolation`).
  - [x] Audience and validity date filtering (`STUDENT`, `STAFF`, `ALL`, expiration tracking).
- [x] **Citation-Grounded Assistant (`assistant`) (Rule B2, B3, C1)**
  - [x] Conversational session management under tenant context (`assistant_conversations`, `assistant_messages`).
  - [x] Grounded RAG with citations pointing to official policy: `[Document Title - Source Ref]` (`test_citation_grounded_assistant_high_confidence`).
  - [x] Confidence-Aware Routing:
    - High Confidence (>= 0.50): `DIRECT_ANSWER` citing official handbook guidelines.
    - Medium Confidence (0.25..0.49): `ROUTE_TO_DEPT` qualified answer recommending department advisor.
    - Low Confidence (< 0.25): `PROPOSED_DRAFT` anti-hallucination ticket generation (`test_citation_grounded_assistant_low_confidence_escalation`).
- [x] **Confirmed Draft Actions & Human-in-the-Loop Safety (Rule B2, B4)**
  - [x] AI assistant produces explicit draft ticket proposals without taking unauthorized automated action.
  - [x] Explicit student/human confirmation required to materialize and dispatch grievance tickets (`handleConfirmAiDraftAction`).
- [x] **Phase 3 Database Schema & Forced RLS (NR-9 & TN-1..TN-4)**
  - [x] Migration `0abc6c41ef9a_create_phase3_campus_ai_schema.py` applied with `FORCE ROW LEVEL SECURITY` across all 4 new tenant tables (`knowledge_documents`, `document_chunks`, `assistant_conversations`, `assistant_messages`).
  - [x] Downgrade to Phase 2 head and re-upgrade to Phase 3 head verified cleanly.
  - [x] Introspection test verifies all 21 tenant tables enforce forced RLS.
- [x] **Phase 3 Frontend Integration**
  - [x] Typed OpenAPI TypeScript client updated with knowledge and assistant endpoints (`client.ts`).
  - [x] Interactive Campus AI persona view with verified institutional knowledge explorer and real-time chat interface.
  - [x] Verified citation chips, grounding confidence score meters, and interactive confirmed draft action cards.
  - [x] Persistent floating slide-over AI assistant drawer accessible from any screen/persona.
  - [x] Production build verified with 0 errors (`npm run build`).

---

## Slice Log & Evidence Registry

| Date | Slice ID | Description | Requirement IDs | Test / Verification Evidence | Status |
|------|----------|-------------|-----------------|------------------------------|--------|
| 2026-10-27 | SLICE-00 | Workspace inspection, Git init, PostgreSQL 18 cluster setup on port 5433, migrator & app roles | NR-1, NR-2, TN-3 | DB created; roles `campuscare_migrator` & `campuscare_app` provisioned | Completed |
| 2026-10-27 | SLICE-01 | Architecture foundation: Alembic initial schema with forced RLS, boundary linter, auth engine, deterministic what-if calculator, offline sync outbox, Next.js portal | NR-1, NR-2, NR-3, NR-5, NR-7, NR-9, TN-1..TN-5, AZ-1..AZ-6, BR-1..BR-3, B3, C5, C7 | 10/10 Pytest tests passing; Next.js 16 build successful; API serving HTTP 200 on port 8000; Web serving HTTP 200 on port 3000 | Completed |
| 2026-10-27 | SLICE-02 | Core workflows: Complaints with SLA promise & closed-loop confirmation, anonymous feedback with physical unlinkability & k>=5, offline attendance sync batch with concurrency detection, outbox worker with dead-letter queue, Next.js UI integration | NR-1, NR-9, NR-10, B3, C7, AZ-6, EV-1..EV-3 | 15/15 Pytest tests passing; Next.js 16 production build passed with 0 errors; Alembic upgrade/downgrade verified | Completed |
| 2026-10-27 | SLICE-03 | Campus AI: Institutional Knowledge base, tenant-isolated vector/hybrid retrieval (TN-6), citation-grounded assistant with confidence-aware routing (B2, B3), anti-hallucination confirmed draft actions (B4), Next.js AI persona and floating drawer | NR-1, NR-9, TN-6, B2, B3, B4, C1 | 18/18 Pytest tests passing; Next.js 16 production build passed with 0 errors; Alembic upgrade/downgrade verified; 21/21 tables forced RLS verified | Completed |

---

## Verification Evidence (Rule NR-1)

### Test Command: `pytest backend/tests/ -v`
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.5, pluggy-1.7.0 -- backend/.venv/Scripts/python.exe
cachedir: .pytest_cache
rootdir: C:\Users\madha\CAMPUSCARE-AI
plugins: anyio-4.15.1, asyncio-0.25.3
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None
collecting ... collected 18 items

backend/tests/test_attendance_whatif.py::test_attendance_what_if_surplus PASSED [  5%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_deficit PASSED [ 11%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_exactly_on_target PASSED [ 16%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_zero_classes PASSED [ 22%]
backend/tests/test_attendance_whatif.py::test_attendance_what_if_invalid_inputs PASSED [ 27%]
backend/tests/test_authorization_matrix.py::test_routes_declare_required_permission PASSED [ 33%]
backend/tests/test_authorization_matrix.py::test_permission_matrix_cross_role_and_cross_tenant PASSED [ 38%]
backend/tests/test_boundaries_linter.py::test_modular_monolith_boundary_linter PASSED [ 44%]
backend/tests/test_campus_ai_assistant.py::test_knowledge_ingestion_and_cross_tenant_grounding_isolation PASSED [ 50%]
backend/tests/test_citation_grounded_assistant_high_confidence PASSED [ 55%]
backend/tests/test_citation_grounded_assistant_low_confidence_escalation PASSED [ 61%]
backend/tests/test_complaints_workflows.py::test_complaints_service_promise_and_closed_loop_lifecycle PASSED [ 66%]
backend/tests/test_feedback_anonymity.py::test_anonymous_feedback_physical_unlinkability_and_k_anonymity PASSED [ 72%]
backend/tests/test_offline_attendance_sync.py::test_offline_attendance_sync_and_optimistic_concurrency PASSED [ 77%]
backend/tests/test_outbox_worker.py::test_outbox_worker_happy_path PASSED [ 83%]
backend/tests/test_outbox_worker.py::test_outbox_worker_retry_and_dead_letter_queue PASSED [ 88%]
backend/tests/test_rls_catalog_introspection.py::test_catalog_introspection_enforces_forced_rls PASSED [ 94%]
backend/tests/test_rls_catalog_introspection.py::test_tenant_isolation_fails_closed_and_isolates_data PASSED [100%]

============================= 18 passed in 1.43s ==============================
```

### Build Command: `npm run build` in `frontend`
```text
▲ Next.js 16.4.3 (Turbopack)
✓ Running next.config.ts took 38ms
- Cache Components enabled
- Partial Prefetching enabled

  Creating an optimized production build ...
✓ Compiled successfully in 1178ms
  Running TypeScript ...
  Finished TypeScript in 3.2s ...
  Collecting page data using 5 workers ...
  Generating static pages using 5 workers (0/4) ...
  Generating static pages using 5 workers (1/4) 
  Generating static pages using 5 workers (2/4) 
  Generating static pages using 5 workers (3/4) 
✓ Generating static pages using 5 workers (4/4) in 960ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
└ ○ /_not-found

○  (Static)  prerendered as static content

Exit code: 0
```

