# ADR 002: Modular Monolith Architecture and Boundary Enforcement

## Status
Accepted

## Context
Educational institutions require integrated capabilities: identity, roster management, attendance tracking, complaint tracking, anonymous feedback, and AI assistance. While microservices offer decoupled teams, they introduce severe operational costs (distributed transactions, partial failures, network latency, multiple databases, container orchestration overhead). Conversely, an unstructured monolith tends to devolve into tightly coupled spaghetti where tables are joined arbitrarily across boundaries.

## Decision
We adopt a **Modular Monolith** architecture with 12 strictly bounded domain modules:
1. `identity`: Users, verification, sessions, MFA.
2. `tenancy`: Colleges, domains, settings.
3. `access`: Roles, grants, attributes, policy decisions, approvals.
4. `directory`: Departments, programs, terms, classes, rosters, enrolments.
5. `attendance`: Sessions, records, corrections, percentage engine.
6. `complaints`: Complaints, assignments, events, SLA clocks, attachments.
7. `feedback`: Cycles, participation, responses, summaries.
8. `notifications`: Preferences, templates, delivery logs.
9. `knowledge`: Documents, versions, chunks, embeddings.
10. `assistant`: Conversations, tools, citations, drafts.
11. `analytics`: Aggregates, forecasts, clustering.
12. `audit`: Append-only, hash-chained tamper-evident audit ledger.

### Architectural Rules:
- **BR-1**: Each module exposes a well-defined Python service interface (`service.py`) and publishes domain events. External modules must never query or import its SQLAlchemy models or database tables directly.
- **BR-2**: Boundary rules are strictly enforced by an automated static analysis test in CI (`test_boundaries_linter.py`). Build fails immediately upon any prohibited cross-domain import.
- **BR-3**: Cross-module side effects (notifications, indexing, SLA clocks) are dispatched through a **Transactional Outbox** (`EV-1`), ensuring atomic state transitions and zero cross-module direct side effects inside an HTTP request.

## Consequences
### Positive
- Single deployable unit, minimal infrastructure (one DB, single process or worker).
- Clean domain separation allows future refactoring or extraction if ever warranted.
- High developer velocity with deterministic transactions and strong consistency.

### Negative
- Developers must maintain strict discipline around service interfaces and event payloads.
