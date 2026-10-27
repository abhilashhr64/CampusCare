# ADR 003: Session Management and Authentication Hardening

## Status
Accepted

## Context
Privilege escalation and unauthorized session hijacking in higher education environments can compromise student privacy, attendance records, and grievance filings. Stateless JWTs stored in client-side storage (localStorage) cannot be revoked instantly upon account compromise, role revocation, or administrative termination.

## Decision
We implement a **server-side revocable session architecture** with multi-factor authentication for staff:
1. **Server-Side Sessions**:
   - Session identifiers are generated as high-entropy cryptographically secure random tokens (32 bytes / 256 bits).
   - Only the SHA-256 hash of the session token is stored in the database (`identity_sessions`).
   - The plain session token is delivered to the browser exclusively via `httpOnly`, `Secure`, `SameSite=Lax` cookies with strict CSRF protection.
   - Any role grant revocation (`AZ-5`), password change, or administrative lockout instantly invalidates all active sessions for the target user.
2. **Deny-by-Default Privilege Escalation (Rule NR-5)**:
   - Verifying an email domain (`@college.edu`) or one-time code only establishes proof of email ownership.
   - It NEVER automatically bestows staff, lecturer, or administrative privileges.
   - Staff roles require explicit approval grants (`access_grants`) provisioned by authorized administrators.
3. **Multi-Factor Authentication (MFA)**:
   - Staff roles (Lecturer, Department Admin, College Admin, Committee Member) require mandatory RFC 6238 TOTP MFA.
   - Step-up re-authentication is required before executing sensitive operations (role approval, complaint closures, data exports).
4. **Admin Bootstrapping**:
   - The root college administrator is provisioned solely via a trusted local CLI command (`python -m src.cli create-admin`) or cryptographically signed time-limited invitation. There is no open public signup route for administrative roles.

## Consequences
### Positive
- Instant session revocation capability across all devices.
- Protection against XSS-based token theft (no tokens stored in localStorage/sessionStorage).
- Compliance with stringent student data protection and institutional governance guidelines.

### Negative
- Requires a database lookup on authenticated requests (mitigated by fast indexed session queries).
