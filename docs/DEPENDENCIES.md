# CampusCare AI — Pinned Dependencies & Justifications

In accordance with requirement **A3.8**, all dependencies are documented with version numbers, rationale, and security audit status.

## Backend (Python 3.12)

| Dependency | Version | Purpose / Rationale |
|---|---|---|
| `fastapi` | `0.115.11` | High-performance async web framework with automated OpenAPI contract generation. |
| `uvicorn[standard]` | `0.34.0` | ASGI server for FastAPI. |
| `pydantic` | `2.10.6` | Data validation, domain schemas, and serialization with type safety. |
| `pydantic-settings` | `2.8.1` | Environment variable parsing and typed application settings. |
| `sqlalchemy` | `2.0.38` | ORM & query builder with support for PostgreSQL schemas, connection pooling, and transaction events. |
| `alembic` | `1.14.1` | Database migration framework with version tracking and upgrade/downgrade scripts. |
| `psycopg[binary]` | `3.2.5` | Official modern PostgreSQL driver with native support for PostgreSQL 18, composite keys, and set_config. |
| `bcrypt` | `4.3.0` | Secure password and token hashing using modern OpenBSD blowfish key derivation. |
| `passlib[bcrypt]` | `1.7.4` | Password context abstraction. |
| `pyotp` | `2.9.0` | RFC 6238 TOTP engine for staff Multi-Factor Authentication. |
| `pytest` | `8.3.5` | Testing framework for unit, integration, and policy matrix tests. |
| `pytest-asyncio` | `0.25.3` | Async test runner for testing FastAPI routes and DB transactions. |
| `httpx` | `0.28.1` | Async HTTP client for end-to-end API test invocations. |
| `python-multipart` | `0.0.20` | Form and file upload parsing for FastAPI. |

## Frontend (Node.js 24 / Next.js 15)

| Dependency | Version | Purpose / Rationale |
|---|---|---|
| `next` | `15.2.4` | App router framework with server components and streaming. |
| `react` / `react-dom` | `19.0.0` | Core UI library. |
| `typescript` | `5.8.2` | Strict type checking. |
| `tailwindcss` | `3.4.17` | Utility-first styling with custom design tokens. |
| `lucide-react` | `0.477.0` | Consistent, accessible icon set. |
| `@tanstack/react-query` | `5.67.1` | Server state management, caching, optimistic updates, and background refetching. |
| `dexie` | `4.0.11` | IndexedDB client library for offline attendance storage and outbox synchronization. |
| `zod` | `3.24.2` | Runtime schema validation for forms and API contracts. |
| `react-hook-form` | `7.54.2` | Form management with fast re-renders and Zod resolver. |
| `clsx`, `tailwind-merge` | Latest | Conditional styling and Tailwind class merging utilities. |
