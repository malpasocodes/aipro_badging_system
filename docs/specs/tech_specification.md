# Technical Specifications
**Badging System**  
**Stack:** Python • Streamlit • uv (venv + package mgmt) • Render (deployment) • Google Identity Services (OAuth)  
**Doc Version:** 1.0 • **Date:** 2025-09-27

---

## 1) Architecture Overview
**Pattern:** Streamlit front-end with embedded service layer + data access layer (DAL).  
**Runtime:** Single Render Web Service (auto-scaled), backing Postgres DB, optional Redis (future).  
**Key Modules:**
- `app/routers`: page controllers (Home, Badges, Approvals, Admin, Profile).
- `app/services`: domain services (auth, onboarding, badges, approvals, exports, audit).
- `app/dal`: repositories / DB access.
- `app/models`: pydantic models & ORM schema.
- `app/ui`: UI helpers, components, theming.
- `app/core`: config, logging, security, utils.
- `tests`: unit, integration, e2e (Playwright optional).

**Data Flow:**  
Google OAuth → session bootstrap → service call → repository → Postgres → response → UI update.  
**State:** `st.session_state` for UI + server-side session (signed cookies / JWT-lite for role & user id).

---

## 2) Data Model (Relational Schema)
**Conventions:** snake_case tables; `id` as UUIDv4; timestamps `created_at`, `updated_at` (UTC).  
Primary tables:
- **users** (`id`, `google_sub`, `email`, `username`, `substack_email`, `meetup_email`, `role` ENUM[`admin`,`assistant`,`student`], `is_active` BOOL, `last_login_at` TIMESTAMP)
- **programs** (`id`, `title`, `description`, `is_active` BOOL)
- **skills** (`id`, `program_id` FK, `title`, `description`, `is_active` BOOL, `position` INT)
- **mini_badges** (`id`, `skill_id` FK, `title`, `description`, `is_active` BOOL, `position` INT)
- **capstones** (`id`, `program_id` FK, `title`, `description`, `is_required` BOOL)
- **requests** (`id`, `user_id` FK, `mini_badge_id` FK, `status` ENUM[`pending`,`approved`,`rejected`], `submitted_at`, `decided_at`, `decided_by` FK users, `reason` TEXT)
- **awards** (`id`, `user_id` FK, `type` ENUM[`mini_badge`,`skill`,`program`], `ref_id` UUID (mini_badge/skill/program id), `awarded_at`)
- **audit_logs** (`id`, `actor_user_id` FK, `action` TEXT, `entity` TEXT, `entity_id` UUID, `metadata` JSONB, `created_at`)
- **notifications** (`id`, `user_id` FK, `type` TEXT, `payload` JSONB, `is_read` BOOL, `created_at`)
- **exports** (`id`, `actor_user_id` FK, `dataset` TEXT, `pii_included` BOOL DEFAULT FALSE, `row_count` INT, `created_at`)

**Derived Views (DB views or materialized views later):**
- `v_user_progress` (percent completion by program/skill).

**Indexes:**
- `users(email)`, `users(google_sub)` unique.  
- Foreign-key indexes on all FK columns.  
- `requests(status, submitted_at)`, `awards(user_id, type, ref_id)`, `audit_logs(created_at)`.

**PII Redaction Strategy:**
- PII columns: `email`, `substack_email`, `meetup_email`.  
- Never included in exports (v1).  
- Masking helpers for UI: `al***@domain.com`.

---

## 3) Role-Based Access Control (RBAC)
**Roles:** `admin`, `assistant`, `student`  
**Matrix (selected):**
- Catalog CRUD: **admin** only.  
- Approve/Reject requests: **admin, assistant**.  
- Exports: **admin** only.  
- Retire badges/programs: **admin** only.  
- Roster role changes: **admin** only.  
- Delete accounts: **n/a** (not permitted in v1).

**Enforcement:**  
- Server-side guard in services; UI hides disallowed actions.  
- Audit every privileged operation.

---

## 4) Business Rules
- Program → Skills → Mini-badges is a strict DAG; prevent cycles.  
- **Skill award** occurs when **all** child mini-badges are approved.  
- **Program award** occurs when **all** skills are awarded (+ optional capstone).  
- Requests are immutable after decision; updates require a new request.  
- No expiration for awards.  
- Evidence storage is out-of-scope (v1).

---

## 5) APIs & Service Interfaces
Although Streamlit runs in-process, expose clear service boundaries for testability.

**AuthService**
- `get_or_create_user(google_sub, email) -> User`
- `require_role(*roles) -> decorator`

**OnboardingService**
- `update_onboarding(user_id, substack_email, meetup_email, username)`

**CatalogService**
- `list_programs()`, `get_program(id)`, `create_program(data)`, `update_program(id, data)`, `toggle_program(id, active)`  
- analogous for `skills`, `mini_badges`, `capstones`

**ProgressService**
- `get_user_progress(user_id) -> ProgressSummary`
- `recompute_awards(user_id)` (idempotent)

**RequestService**
- `submit_request(user_id, mini_badge_id)`  
- `list_requests(filters)`, `get_request(id)`  
- `decide_request(id, approver_id, decision, reason=None)`

**ExportService**
- `preview(dataset, filters) -> rows_masked`  
- `export(dataset, filters) -> CSVBytes` (PII stripped)  
- Logs to `exports` & `audit_logs`

**NotificationService**
- `notify(user_id, type, payload)`  
- `list_notifications(user_id)` → simple in-app list

---

## 6) Security
- **OAuth:** Google Identity Services with PKCE.  
- **Sessions:** signed cookie (httpOnly, secure); store `user_id`, `role`, `nonce`.  
- **CSRF:** Streamlit forms + server checks on state token.  
- **Secrets:** Render env vars; never commit secrets.  
- **Input Validation:** pydantic models for all service inputs.  
- **DB:** least-privilege DB user; parameterized queries.  
- **Audit:** all privileged ops (approve/reject, export, role change, catalog CRUD).  
- **Backups:** Render Postgres automated backups (daily); retain 7–30 days.  
- **PII:** export pipeline strips PII; UI masking; logs never include PII.

---

## 7) Performance & Scalability
- **Targets:** p95 page render < 800ms (cached), < 1500ms (cold).  
- **Pagination:** all tables default 25 rows; lazy load next pages.  
- **Query Optimization:** indexes (above), selective columns, `LIMIT/OFFSET`.  
- **Caching:** `st.cache_data` for read-only catalog; TTL 5m.  
- **Cold Start:** pre-warm DB connection on app start.  
- **Batch Ops:** avoid `N+1` queries; use `IN` queries and joins.  
- **Future:** add Redis for shared cache when scaling multiple instances.

---

## 8) Observability
- **Logging:** structlog/standard logging with JSON formatter.  
- **Levels:** INFO for user events, DEBUG for dev only (guarded by env).  
- **Tracing:** request id per user action; include in audit.  
- **Metrics:** counters for sign-ins, submissions, decisions, exports, errors.  
- **Health Check:** `/healthz` lightweight route returning DB liveness.  
- **Alerts:** Render health checks + log-based alerts for ERROR spikes.

---

## 9) Packaging & Dependencies
- **Python:** 3.11+  
- **Tooling:** uv for env + lockfile (`uv.lock`).  
- **Structure:**  
  ```
  /app
    /core
    /ui
    /models
    /services
    /dal
    /routers
  /tests
  pyproject.toml
  uv.lock
  README.md
  ```
- **Key deps:** streamlit, psycopg / asyncpg, pydantic, SQLModel or SQLAlchemy, python-dotenv (dev), structlog.  
- **Dev deps:** pytest, pytest-asyncio, coverage, ruff, mypy, pre-commit.

---

## 10) Database & Migrations
- **Engine:** Postgres 14+ (Render).  
- **Migrations:** Alembic (if using SQLAlchemy/SQLModel).  
- **Naming:** meaningful revision messages; one feature per migration.  
- **Seed:** admin bootstrap script creating initial `admin` user via email allowlist.

---

## 11) Deployment (Render)
- **Services:**  
  - Web Service: Streamlit (`streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`)  
  - Postgres: Managed Render PostgreSQL
- **Build:**  
  - Build Command: `uv sync --frozen`  
  - Start Command: `uv run streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`
- **Env Vars:**  
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`  
  - `DATABASE_URL`  
  - `APP_SECRET_KEY`  
  - `APP_ENV` (`prod|staging|dev`)  
  - `LOG_LEVEL`
- **Health Checks:** `/healthz` every 30s; failure threshold 3 → restart.

---

## 12) CI / CD
- **CI (GitHub Actions):**
  - lint (ruff), type-check (mypy), tests (pytest), coverage ≥ 80%  
  - `uv sync --frozen` to ensure lock reproducibility
- **CD:** Render auto-deploy on main; manual promotion to prod (protected branch).  
- **Artifacts:** coverage report, packaged app (optional).

---

## 13) Testing Strategy
- **Unit:** services with mocked DAL.  
- **Integration:** DAL against test Postgres (Docker).  
- **E2E:** Playwright (optional) for critical flows (sign-in stub, request/approve/export).  
- **Security tests:** role guard tests, PII redaction tests, export tests.  
- **Load tests:** basic concurrency for approvals & exports.

**Acceptance (sample):**
- Submitting a request inserts `requests` row (pending) and audit entry.  
- Approving creates award(s) as rules dictate and notifies student.  
- Export excludes PII columns and logs `exports` + `audit_logs` entries.

---

## 14) Error Handling
- Map service exceptions to user-facing messages.  
- Retry transient DB errors (exponential backoff).  
- Circuit-breaker (simple) for DB unavailability to show friendly downtime page.

---

## 15) Security & Privacy Reviews
- Pre-launch review checklist: OAuth scopes, secret storage, least privilege DB user, audit coverage, export redaction, log scrubbing, dependency audit (`uv pip audit` or `pip-audit`).

---

## 16) Roadmap Hooks (Post‑v1)
- Evidence uploads (S3-compatible storage) with signed URLs.  
- Email notifications via transactional provider.  
- Open Badges issuance (W3C).  
- Redis cache + multi-instance scaling.  
- Fine-grained permissions (policy engine).

---

**End of Technical Specifications**
