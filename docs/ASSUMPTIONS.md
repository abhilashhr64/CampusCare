# CampusCare AI — Assumptions & Architectural Defaults

This document records architectural defaults, operational choices, and baseline assumptions in accordance with requirement **A3.9** of the Master Prompt.

## 1. Tenancy & Infrastructure
- **PostgreSQL 18 Instance**: Local dedicated cluster runs on port `5433` (`c:\Users\madha\campuscare_pgdata`) to avoid port collisions with existing Windows services.
- **Tenant Context Variable**: Transactions set session-local configuration via `SET LOCAL app.current_college_id = '...'` and `SET LOCAL app.current_user_id = '...'`. Missing configuration causes queries against tenant tables to fail closed (returning 0 rows or rejecting inserts/updates).
- **Separation of Roles**:
  - `campuscare_migrator`: Owns database objects, runs Alembic migrations, can create tables and alter RLS policies.
  - `campuscare_app`: The runtime application role. Configured with `NOBYPASSRLS`. Cannot bypass Row Level Security.
- **Storage**: S3-compatible local/cloud storage bucket with signed URLs (15-minute expiry).

## 2. Authentication & Authorization
- **Session Model**: Server-side revocable session tokens stored in `identity_sessions` with hashed session keys. Frontend holds secure `httpOnly`, `SameSite=Lax`, `Secure` cookie.
- **Privilege Separation**: Verified email permits only account creation and basic student identity binding against imported rosters. Staff and administrative roles require explicit administrative approval grants (`access_grants`).
- **MFA Requirement**: TOTP-based Multi-Factor Authentication mandatory for all staff roles (Lecturer, Department Admin, College Admin, Grievance Committee, Operator).
- **Centralized Policy Engine**: Every route and tool calls `authorize(actor, action, resource)`. Deny-by-default.

## 3. Feedback Anonymity Design (NR-10)
- **Zero Stored Link**: To guarantee unlinkability by design, student submission uses a two-phase blinded ticket model:
  1. A student marks their cycle participation in `feedback_participation` (recording `has_submitted = true` to prevent duplicate submissions).
  2. The response content is written to `feedback_responses` without any `user_id`, session ID, or join key.
  3. Batch insertion / randomized delay jitter prevents timing-based correlation between participation and response rows.
  4. Aggregates are only exposed to lecturers if a subject has >= 5 student responses (k-anonymity threshold).

## 4. Offline Attendance Protocol (C7)
- **Client Storage**: Dexie.js (IndexedDB) holds pending attendance operations with `op_id` (UUID), `base_version`, and action payload.
- **Server Ingestion**: The batch sync endpoint evaluates `op_id` idempotency and `base_version` concurrency. Mismatches return conflicts without silent overwrite.

## 5. Audit Logging (B3)
- **Hash-Chained Audit Ledger**: Every privileged action (role grants, attendance revisions, complaint status overrides) appends a record with `prev_hash`, `payload_hash`, and `entry_hash = SHA256(prev_hash + payload + timestamp)` to guarantee tamper evidence.
