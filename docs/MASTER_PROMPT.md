# CampusCare AI — Master Development Prompt (v2, advanced)

**How to use:** paste this whole document into your coding agent at the repository root and save a copy as docs/MASTER_PROMPT.md. The agent keeps docs/PROGRESS.md current and cites requirement IDs (NR-1, ID-3, AT-2 and so on) in commits, tests and reports. Treat every numbered rule as testable.

## Part A: Operating contract

### A1. Role and mission

Act as one senior team: software architect, full-stack engineer, UI/UX designer, database engineer, AI/ML engineer, security engineer and DevOps engineer.

Build **CampusCare AI**, a production-oriented, multi-tenant college services platform: verified identity, role-approved staff, complaint workflows, attendance, anonymous teacher feedback, a citation-grounded AI assistant and analytics. Inspect the repository, plan, write working code, run it, test it, fix it and document it. Do not deliver static mock-ups, frontend-only prototypes or disconnected pages.

Order of work: **reliable workflows first, trustworthy AI second, predictive intelligence third.**

### A2. Non-negotiable rules

| ID | Rule |
| --- | --- |
| NR-1 | Never claim a feature is implemented or tested unless you ran it. Report the command and its actual result. |
| NR-2 | Tenant isolation is enforced by PostgreSQL row-level security (forced, with a non-owner application role) and again in application code. |
| NR-3 | Authorization is server-side and deny-by-default. Hiding a menu item is cosmetic, never a control. |
| NR-4 | AI never writes official records. It drafts; a human confirms; the backend executes under that human's permissions and re-checks them. |
| NR-5 | A verified email address alone never grants lecturer, department admin or college admin privileges. |
| NR-6 | Development and tests use synthetic data only. No real student or staff data enters the repository, prompts or logs. |
| NR-7 | No secrets in source control. Provide .env.example and document every variable. |
| NR-8 | The product stays fully usable when the AI provider is down or disabled. AI is an enhancement with fallbacks. |
| NR-9 | Every schema change is an Alembic migration; upgrade and downgrade are tested where feasible. |
| NR-10 | Anonymous feedback has no stored link between respondent identity and answers, by design and not by policy. |
| NR-11 | Never fabricate metrics, benchmarks, test counts or screenshots. Numbers come from scripts in the repository with fixed seeds. |
| NR-12 | Do not start a phase until the previous phase's release gate has passed with evidence. |
| NR-13 | Keep infrastructure minimal: a modular monolith, one database, one cache. No microservices or Kubernetes without a written decision record showing a measured need. |

### A3. Working protocol

1. **Inspect first.** List the tree; read manifests, lockfiles, configs, existing routes, migrations and the README; run existing tests and note the baseline. Report what works, what is missing and what is risky before changing anything.
2. **Plan in the repository.** Write a phased checklist to docs/PROGRESS.md and keep it current after every slice.
3. **Decision records.** For every security-critical, irreversible or expensive-to-change choice (tenancy model, auth flow, session design, anonymity design, AI provider boundary), add docs/adr/NNN-title.md with context, options, decision and consequences.
4. **Vertical slices.** Build one slice end to end in this order: migration, model, policy rules, API, regenerated contract, UI, tests, docs.
5. **Test and fix loop.** Run the relevant tests after every slice and fix failures before moving on. After three failed attempts at the same problem, stop, record the blocker and evidence in docs/PROGRESS.md, and continue with an independent task.
6. **Small commits.** Conventional commit messages, one slice per branch, no unrelated changes in a commit.
7. **Read before writing.** Never overwrite a working file you have not read. Reuse sound existing code.
8. **Dependencies.** Check official documentation and compatibility before installing, pin versions, record each dependency and its reason in docs/DEPENDENCIES.md, and run vulnerability audits in CI.
9. **Ambiguity.** Choose the safest reasonable default, record it in docs/ASSUMPTIONS.md and continue. Ask the human only when the answer blocks progress and concerns security, legal or consent.
10. **Stop and ask before:** destructive data operations, production deployments, anything that spends money, legal or consent decisions, and schema choices that cannot be migrated back.

### A4. Definition of done for every slice

- [ ] Behaviour is implemented against real persistence, not mock data.
- [ ] The migration applies cleanly on an empty database and on the previous schema.
- [ ] Policy rules have allow and deny tests, including cross-college denial.
- [ ] The API is documented in OpenAPI and the TypeScript client is regenerated and committed.
- [ ] The UI has loading, empty, error, offline and permission-denied states, and is keyboard and screen-reader checked.
- [ ] Unit and integration tests pass; user journeys have Playwright tests.
- [ ] Audit events are emitted for privileged actions.
- [ ] Logs contain no secrets or personal data.
- [ ] README, API notes and docs/PROGRESS.md are updated.

### A5. Reporting format after each slice

1. **Done:** what now works, with requirement IDs.
2. **Evidence:** exact commands run and a summary of their real output (tests passed and failed, coverage, scan results).
3. **Not done:** anything partial, skipped or stubbed, stated plainly.
4. **Risks and assumptions:** new or changed.
5. **Next:** the next slice and why.

CI generates the test report into docs/reports/. It must never be edited by hand.

## Part B: Product scope

### B1. Personas

| Persona | Core job | Home screen must answer |
| --- | --- | --- |
| Student | Know attendance, raise and track issues, get verified answers | Am I safe on attendance? What is pending? What changed? |
| Lecturer | Mark attendance fast, see own feedback themes | Which class is next? Who is repeatedly absent? |
| Department admin | Clear the complaint queue before deadlines breach | What is at risk today? Who is overloaded? |
| College admin | Onboard, approve, configure, see institution patterns | Who needs approval? Which issues recur? |
| Platform operator | Operate many colleges safely | Is every tenant healthy, isolated and backed up? |
| Grievance committee member | Handle sensitive cases under restriction | What needs a human response now? |

### B2. Release scope

| Release | Contents |
| --- | --- |
| MVP (phases 1 and 2) | Tenants, verified signup, roster matching, role approval, dashboards, complaints, attendance with offline drafts, feedback, notifications, audit |
| Campus AI (phase 3) | Knowledge base, cited assistant, confidence-aware routing, multilingual input, confirmed draft actions |
| Intelligence (phase 4) | Duplicate detection, feedback themes, SLA risk, recurring-issue analytics, supportive attendance alerts |
| Pilot (phase 5) | One college, two or three departments, AI in shadow mode, measured outcomes |

### B3. Signature capabilities

- **Service promise:** every request shows a committed response time and an owner at submission, with a visible countdown.
- **Attendance what-if:** the exact classes a student must attend or can miss per subject (deterministic, tested, no AI).
- **Location-tagged reporting:** QR codes on classrooms, hostel blocks, labs and buses prefill location and category.
- **Tamper-evident audit:** attendance corrections, complaint closures and role approvals are hash-chained so silent alteration is detectable.
- **Closed-loop resolution:** students confirm or reopen resolutions, and the outcome feeds quality metrics and routing evaluation.
- **Institutional memory (staff):** cited, privacy-safe retrieval of similar past complaints and what resolved them (phase 3 or 4).

### B4. Explicit non-goals for the first release

Payments or fee collection, grades and examination marks, automated disciplinary or admission decisions, mandatory GPS tracking, face recognition or proctoring, scraping external sites at answer time, and training external models on student data. QR attendance and other opt-in mechanisms may come later as policy-controlled options.

## Part C: Architecture and technology

### C1. Mandatory stack

Use stable, compatible releases, pin versions in manifests and lockfiles, and verify compatibility against official documentation before installing.

| Layer | Required technology |
| --- | --- |
| Frontend | Next.js App Router, React, TypeScript (strict), Tailwind CSS, shadcn/ui with Radix UI, TanStack Query, React Hook Form with Zod, Storybook, installable PWA, Dexie (IndexedDB) for offline attendance |
| Frontend structure | Feature-Sliced Design: app, pages, widgets, features, entities, shared |
| Frontend tests | Vitest, Playwright, axe-core accessibility checks |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic, OpenAPI-generated TypeScript client |
| Data | PostgreSQL with forced row-level security, pgvector, pg_trgm |
| Jobs and cache | Redis with Arq or Celery workers |
| Files | S3-compatible object storage, malware scan, signed short-lived URLs |
| Identity | OIDC/SSO where available, verified email link or one-time code as fallback, roster matching, staff MFA, revocable server-side sessions |
| AI | Provider-independent gateway, hybrid retrieval, reranker, task-specific classifiers, structured outputs |
| Operations | Docker and Docker Compose, GitHub Actions, separate local, staging and production configuration, OpenTelemetry, error monitoring, feature flags, automated backups with a documented restore |

### C2. Modular monolith and module boundaries

Organise the backend as one deployable with strictly separated modules.

| Module | Owns |
| --- | --- |
| identity | Users, verification, sessions, MFA |
| tenancy | Colleges, domains, settings, configuration versions |
| access | Roles, grants, attributes, policy decisions, approvals |
| directory | Departments, programs, terms, classes, rosters, enrolments |
| attendance | Sessions, records, corrections, percentage engine |
| complaints | Complaints, assignments, events, SLA clocks, attachments |
| feedback | Cycles, participation, responses, summaries |
| notifications | Preferences, templates, delivery log |
| knowledge | Documents, versions, chunks, embeddings |
| assistant | Conversations, tools, citations, drafts |
| analytics | Aggregates, forecasts, clustering outputs |
| audit | Append-only, hash-chained audit events |

**BR-1.** Each module exposes a service interface and publishes events. Other modules never read its tables directly.

**BR-2.** Enforce boundaries with an automated import-linter or equivalent contract in CI; a violation fails the build.

**BR-3.** Cross-module side effects (notifications, indexing, SLA timers) go through the transactional outbox, never through direct calls inside a request.

### C3. Tenancy design

- **TN-1.** Every tenant-owned table has a non-null college_id. Foreign keys between tenant tables are composite (college_id, id) so a row can never reference another college's row.
- **TN-2.** Each request or job runs in a transaction that sets the tenant and actor with set_config(..., true) (transaction-local). Code must fail closed if the setting is missing.
- **TN-3.** The application connects as a non-owner role without BYPASSRLS. Migrations use a separate privileged role. FORCE ROW LEVEL SECURITY is enabled on every tenant table.
- **TN-4.** A CI test introspects the catalog and fails if any table with college_id lacks enabled and forced RLS policies for select, insert, update and delete.
- **TN-5.** Platform-operator access across tenants uses a separate, audited break-glass path with a reason, an expiry and an alert. It is never part of the normal role set.
- **TN-6.** Vector search, full-text search, exports, report queries and background jobs all run under the same tenant context. Embeddings are filtered by college, audience and validity date before ranking.

### C4. Authorization

- **AZ-1.** Implement a single policy decision function authorize(actor, action, resource) returning allow or deny, a reason code and any obligations (for example, mask fields, require reason). All routes and AI tools call it.
- **AZ-2.** Combine RBAC (roles) with ABAC (department, assigned class, complaint sensitivity, ownership, time window, purpose).
- **AZ-3.** Every route declares its required permission. A CI test enumerates all routes and fails if any lacks a declaration.
- **AZ-4.** Generate a permission matrix test automatically: for each role, each endpoint and each of two tenants, assert the expected allow or deny.
- **AZ-5.** Role grants carry approver, reason, scope and expiry. Revocation invalidates active sessions immediately.
- **AZ-6.** A lecturer sees only assigned classes and the students enrolled in them. Individual feedback is never visible to lecturers; only thresholded aggregates.

### C5. Sessions and identity hardening

- Store sessions server-side for revocation; use httpOnly, Secure, SameSite cookies with CSRF protection, short access lifetimes and rotating refresh credentials.
- Require MFA (TOTP or WebAuthn) for every staff role; step-up authentication for approvals, exports and policy changes.
- Rate-limit and monitor sign-in, verification and password-less code flows; use constant-time comparisons and single-use, expiring tokens.
- Provision the first college admin only through a trusted onboarding command or signed invitation. There is no public path to an admin role.

### C6. Events and background work

- **EV-1.** Use a transactional outbox: the state change and its event commit together.
- **EV-2.** Consumers are idempotent (deduplicate by event id), retry with exponential backoff, and move poison messages to a dead-letter table with an alert.
- **EV-3.** SLA timers, notifications, document indexing and analytics refresh run as workers, never inside the request path.

### C7. Offline attendance synchronisation protocol

1. The client stores each action as an outbox entry: op_id (UUID), type, payload, base_version, created_at and device_id, in IndexedDB.
2. The client sends batches to a sync endpoint. For every entry the server returns exactly one outcome: applied, duplicate (already applied, same op_id), conflict or rejected with a reason.
3. A conflict occurs when the server's version of the session or record is newer than base_version. The server never overwrites silently; it returns both versions.
4. The UI shows a sync status chip (synced, pending, failed) and a review screen for conflicts where the lecturer chooses which version stands, with the choice audited.
5. Retries are always safe because of op_id idempotency. Test with network drops mid-batch, duplicate sends, clock skew and two devices editing the same session.
