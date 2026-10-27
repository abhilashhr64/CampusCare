# CampusCare AI — Automated Database Backup & Disaster Recovery Runbook

In accordance with requirement **C1** of the Master Prompt (*"automated backups with a documented restore"*), this document outlines the operational backup architecture, scheduled snapshot procedures, and point-in-time recovery (PITR) runbook for CampusCare AI.

---

## 1. Backup Strategy Overview

| Tier | Frequency | Target / Tool | Retention | Purpose |
|---|---|---|---|---|
| **WAL Archiving** | Continuous (streaming) | S3 / MinIO via `pgBackRest` or `wal-g` | 30 days | Point-In-Time Recovery (PITR) to any second |
| **Full Base Backup** | Daily at 02:00 UTC | `pg_dump` / `pgBackRest` compressed | 90 days | Disaster recovery and cold replica spinning |
| **Audit Ledger Snapshot** | Hourly | Encrypted S3 immutable bucket | 7 years | Tamper-evident regulatory audit trail compliance |

---

## 2. Backup Execution

### Option A: Automated Containerized / CLI Backup
Run the backup script located at `backend/src/scripts/backup.py` or execute:

```bash
# Set database credentials for migrator/admin
export PGPASSWORD="SuperSecretAdminPass123!"

# Full database dump with compression and timestamps
pg_dump -h localhost -p 5432 -U campuscare_admin -F c -b -v \
  -f /backups/campuscare_$(date +%Y%m%d_%H%M%S).dump campuscare
```

---

## 3. Verified Disaster Recovery & Restore Runbook

### Step 1: Pre-Restore Verification
1. Isolate the target cluster from incoming web traffic to prevent inconsistent writes.
2. Ensure target database instance has PostgreSQL 18 installed with `pgvector` and `pg_trgm` extensions.

### Step 2: Database Re-creation
```sql
-- Connect as superuser
DROP DATABASE IF EXISTS campuscare_recovery;
CREATE DATABASE campuscare_recovery WITH OWNER = campuscare_migrator;
```

### Step 3: Schema & Data Restoration
```bash
pg_restore -h localhost -p 5432 -U campuscare_migrator \
  --clean --if-exists --no-owner --role=campuscare_migrator \
  -d campuscare_recovery /backups/campuscare_YYYYMMDD_HHMMSS.dump
```

### Step 4: Re-apply Roles & RLS Verification
Execute `backend/src/scripts/init_db_roles.sql` to re-assert non-owner application role permissions:
```bash
psql -h localhost -p 5432 -U campuscare_admin -d campuscare_recovery -f backend/src/scripts/init_db_roles.sql
```

### Step 5: Post-Restore Catalog RLS Introspection
Verify all 27 tenant tables enforce `FORCE ROW LEVEL SECURITY`:
```bash
pytest backend/tests/test_rls_catalog_introspection.py -v
```

### Step 6: Audit Chain Integrity Check
Run the cryptographic hash verification on `audit_log_entries` to confirm zero chain tampering during disaster recovery:
```bash
pytest backend/tests/test_pilot_user_journeys.py::test_pilot_audit_ledger_tamper_evidence -v
```
