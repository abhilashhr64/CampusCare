# CampusCare AI — Cloud Production Deployment Guide

This guide details the procedures to take **CampusCare AI** from local development into production on cloud infrastructure, complete with multi-tenant row-level security, Google Institutional OAuth, and zero-downtime deployment pipelines.

---

## 1. System Architecture Overview

```mermaid
graph TD
    Client[Browser / Mobile / PWA] -->|HTTPS :443| CDN[Cloudflare / Cloud Ingress]
    CDN -->|Next.js Web Portal :3000| Frontend[Next.js 16 Production Runner]
    Frontend -->|REST APIs / Cookies| Backend[FastAPI Core Server :8000]
    Backend -->|Alembic Migrations| MigratorRole[DB Role: campuscare_migrator]
    Backend -->|Runtime App Queries| AppRole[DB Role: campuscare_app (NOBYPASSRLS)]
    MigratorRole --> Postgres[(PostgreSQL 16 Multi-Tenant DB)]
    AppRole -->|Forced RLS Filtered| Postgres
    Backend -->|Google Token Verification| GoogleOAuth[Google Identity Platform]
```

---

## 2. Option A: 1-Click Turnkey Deployment on Render

The repository includes a root [render.yaml](file:///c:/Users/madha/CAMPUSCARE-AI/render.yaml) specification that provisions the complete stack with a single click:

1. Push this repository to your GitHub account (`git push origin main`).
2. Log into [Render.com](https://dashboard.render.com).
3. Click **New +** → **Blueprint**.
4. Connect your `CampusCare` repository.
5. Render reads `render.yaml` and provisions:
   - **`campuscare-postgres`**: Managed PostgreSQL 16 database.
   - **`campuscare-backend`**: FastAPI web service running Alembic auto-migrations and Uvicorn.
   - **`campuscare-frontend`**: Next.js 16 web portal with Turbopack production builds.
6. Once deployed, Render provides public HTTPS endpoints (e.g. `https://campuscare-frontend.onrender.com`).

---

## 3. Option B: Deployment on Railway

The repository includes [railway.json](file:///c:/Users/madha/CAMPUSCARE-AI/railway.json):

1. Go to [Railway.app](https://railway.app) and click **New Project** → **Deploy from GitHub repo**.
2. Select `abhilashhr64/CampusCare`.
3. Add a **PostgreSQL** plugin from Railway's template library.
4. Set the following environment variables in the service dashboard:
   ```env
   ENVIRONMENT=production
   DEBUG=false
   APP_SECRET_KEY=<32-character-random-hex-string>
   DB_MIGRATOR_URL=${{Postgres.DATABASE_URL}}
   DB_APP_URL=${{Postgres.DATABASE_URL}}
   ```
5. Railway deploys the backend container and binds the port automatically.

---

## 4. Option C: VPS / Dedicated Server via Docker Compose

To deploy on any Ubuntu/Debian Linux VPS (AWS EC2, DigitalOcean Droplet, GCP Compute Engine, Hetzner):

1. SSH into your server and clone the repository:
   ```bash
   git clone https://github.com/abhilashhr64/CampusCare.git
   cd CampusCare
   ```
2. Copy the production environment template:
   ```bash
   cp .env.production.example .env.production
   ```
3. Generate a cryptographic secret key:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
   Set `APP_SECRET_KEY=<generated-key>` in `.env.production`.
4. Launch the hardened multi-container stack:
   ```bash
   docker compose up --build -d
   ```
5. Check health:
   ```bash
   curl http://localhost:8000/api/v1/system/health
   curl http://localhost:3000
   ```

---

## 5. Configuring Real Google Cloud OAuth 2.0 Credentials

Currently, CampusCare AI validates institutional college emails (`@...edu` or your college domain) and provisions accounts. To link live Google OAuth with token verification:

### Step 1: Create OAuth Credentials in Google Cloud Console
1. Navigate to [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Create a new project named **CampusCare AI**.
3. Configure the **OAuth Consent Screen**:
   - User Type: **Internal** (if Google Workspace for Education) or **External**.
   - App Name: `CampusCare AI`.
   - Authorized Domains: Add your college domain (e.g., `apex.edu`).
4. Click **Create Credentials** → **OAuth Client ID**:
   - Application Type: **Web Application**.
   - Authorized JavaScript Origins: `http://localhost:3000` and your production domain (e.g., `https://campuscare.yourcollege.edu`).
   - Authorized Redirect URIs: `https://campuscare.yourcollege.edu/auth/callback`.
5. Copy your **Client ID** and **Client Secret**.

### Step 2: Set Environment Variables
Add to your production `.env` or cloud secret manager:
```env
GOOGLE_CLIENT_ID=xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 6. PostgreSQL Forced RLS & Multi-Tenancy Verification

Verify that tenant data isolation is mathematically enforced at the PostgreSQL engine level:

```sql
-- Connect via psql to inspect row-level security status
SELECT relname AS table_name, relrowsecurity AS rls_enabled, relforcerowsecurity AS forced_rls
FROM pg_class
WHERE relname IN ('students', 'attendance_records', 'complaints', 'feedback_responses');
```

Expected output:
```text
      table_name       | rls_enabled | forced_rls 
-----------------------+-------------+------------
 students              | t           | t
 attendance_records    | t           | t
 complaints            | t           | t
 feedback_responses    | t           | t
```

---

## 7. Security Hardening Checklist (Production Go-Live)

- [x] **Rule NR-2:** Tenant isolation enforced via composite foreign keys `(college_id, ...)` and PostgreSQL Row Level Security.
- [x] **Rule NR-5:** A verified Google email address alone never grants elevated lecturer or admin roles. Newly provisioned Google accounts strictly default to `STUDENT`.
- [x] **Rule NR-8:** AI Gateway operates asynchronously and fails gracefully if external LLM providers are offline.
- [x] **Rule NR-10:** Anonymous feedback maintains physical unlinkability by design ($k \ge 5$).
- [x] **Rule C5:** Session cookies use `HttpOnly`, `SameSite=Lax`, and `Secure` flags on HTTPS.
