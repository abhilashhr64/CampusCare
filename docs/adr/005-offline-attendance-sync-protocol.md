# ADR 005: Offline Attendance Synchronization Protocol

## Status
Accepted

## Context
Faculty members often take attendance in lecture halls, laboratories, sports grounds, or basements with intermittent, degraded, or zero cellular and Wi-Fi connectivity. Requirement **C7** demands an offline attendance synchronization protocol with client-side outbox storage, server-side idempotency, conflict detection without silent overwrites, and a dispute resolution workflow.

## Decision
We implement the **IndexedDB Outbox & Batch Synchronization Protocol**:
1. **Client-Side Outbox (IndexedDB via Dexie.js)**:
   - When offline, attendance records or corrections are queued locally in an `attendance_outbox` store.
   - Each operation record contains:
     - `op_id`: Client-generated UUIDv4 (idempotency key).
     - `type`: `MARK_SESSION` | `UPDATE_RECORD` | `BULK_MARK`.
     - `payload`: Target session ID, student IDs, status (`PRESENT`, `ABSENT`, `EXCUSED`), notes.
     - `base_version`: Integer tracking the server-side version of the session when the client loaded it.
     - `device_id`: Persistent client installation identifier.
     - `created_at`: Client ISO timestamp.
2. **Server Batch Ingestion Endpoint (`POST /api/v1/attendance/sync`)**:
   - The server processes entries sequentially within a tenant-scoped transaction.
   - For each operation, the server returns exactly one outcome:
     - `applied`: Success; session version incremented; new records persisted.
     - `duplicate`: The `op_id` was already applied previously (safe retry).
     - `conflict`: The server's current session version is strictly greater than `base_version` (another lecturer or office admin modified the session concurrently). Both server and client versions are returned for review.
     - `rejected`: Policy failure (e.g. invalid student enrollment, permission denied).
3. **Conflict Resolution UI & Tamper-Evident Ledger**:
   - Conflicts trigger an explicit review screen in the UI showing the two conflicting states.
   - The instructor selects which version prevails, and the resolution is logged with a cryptographic hash chain in `audit_ledger`.

## Consequences
### Positive
- Zero data loss during network dropouts; fully offline-capable progressive web application (PWA).
- Deterministic conflict handling without silent data corruption or race conditions.

### Negative
- Requires robust client-side storage management and conflict resolution UI.
