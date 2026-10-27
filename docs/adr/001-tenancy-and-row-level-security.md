# ADR 001: Tenancy Isolation Model and PostgreSQL Row-Level Security

## Status
Accepted

## Context
CampusCare AI is a multi-tenant platform designed to serve multiple colleges and universities concurrently. High-stakes educational data (student records, grievance reports, attendance, disciplinary cases, and anonymous feedback) cannot be exposed across tenant boundaries under any circumstances. 

We considered three tenancy architectural models:
1. **Database-per-tenant**: Separate physical PostgreSQL database per college.
2. **Schema-per-tenant**: Single database with a separate PostgreSQL schema per college.
3. **Shared-schema with Forced PostgreSQL Row-Level Security (RLS)**: Single schema with `college_id` partitioned tables, composite foreign keys, and database-enforced row-level security backed by application-level scoping.

## Decision
We adopt **Option 3: Shared-schema with Forced Row-Level Security (RLS) and Composite Foreign Keys**, governed by the following strict rules:
- **Rule TN-1**: Every tenant-owned table must include a non-nullable `college_id` UUID column. All inter-table foreign keys between tenant tables must be composite `(college_id, id)` to prevent any row from referencing an entity belonging to another college.
- **Rule TN-2**: Every request or transaction sets the tenant context via `SET LOCAL app.current_college_id = :college_id`. If this variable is null or missing, queries fail closed (yielding 0 rows or blocking inserts).
- **Rule TN-3**: The runtime application connects using a dedicated non-owner role (`campuscare_app`) that has `NOBYPASSRLS`. Database migrations run as a privileged migrator (`campuscare_migrator`). `ALTER TABLE ... FORCE ROW LEVEL SECURITY` is enabled on every tenant table so that even table owners cannot bypass policies if accidentally connected.
- **Rule TN-4**: A CI introspection test inspects `pg_tables` and `pg_policies` to verify that every table containing `college_id` has forced RLS enabled with active policies for SELECT, INSERT, UPDATE, and DELETE.
- **Rule TN-5**: Cross-tenant platform operator access uses a break-glass audited procedure with explicit reason, short expiry, and audit alerts.

## Consequences
### Positive
- Defense-in-depth: even if an application bug omits a `WHERE college_id = :id` clause, the database kernel drops non-tenant rows.
- Minimal operational complexity: one database cluster, unified Alembic migrations, simple backups and connection pooling.
- Verified in automated CI test suites via catalog introspection.

### Negative
- Requires composite foreign keys on all related tables, increasing index storage slightly.
- Requires transaction-scoped variable setting on every pooled connection acquisition.
