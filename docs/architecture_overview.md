# Architecture & Codebase Overview

_Last updated: October 2025_

This document summarizes the current state of the AIPPRO Badging System codebase,
highlighting major components, data flow, and areas to monitor during future
phases.

## 1. High-Level Architecture
- **Streamlit UI** (`app/ui/`, `app/routers/`) renders dashboards and dialogs for
  admins, assistants, and students. Routing lives in `app/main.py` and
  dispatches to role-specific dashboards.
- **Services layer** (`app/services/`) encapsulates domain logic: authentication,
  onboarding, roster, request queue, catalog, progression, and auditing. Most
  services expect a SQLModel session/engine and perform validation plus logging.
- **Data model** (`app/models/`) uses SQLModel to map programs → skills →
  mini-badges → capstones, requests, awards, users, and audit logs.
- **Core utilities** (`app/core/`) provide configuration (`config.py`), logging
  (`logging.py`), database engine helpers (`database.py`), session helpers
  (`session.py`), and secrets bootstrapping (`secrets_bootstrap.py`).
- **Entry point** – `streamlit_app.py` invokes `app.main.main()`, which handles
  secrets bootstrap, logging setup, configuration loading, authentication check,
  and dashboard routing.

## 2. Authentication & Authorization
- Streamlit native OAuth (`st.login`, `st.user`) is surfaced in
  `app/ui/oauth_auth.py`. Guards detect missing configuration and guide the user.
- `app/core/secrets_bootstrap.ensure_streamlit_secrets_file()` materializes
  `.streamlit/secrets.toml` from `STREAMLIT_AUTH__*` environment variables so the
  Streamlit runtime always sees an auth provider configuration.
- `app/services/oauth.OAuthSyncService` syncs `st.user` data into the database,
  calling `app/services/auth.AuthService` for user creation, role assignment, and
  last-login tracking. Admin bootstrap comes from `ADMIN_EMAILS`.
- Authorization helpers live in `app/services/*` (e.g., request/catalog services
  enforce role checks) and UI guards call `require_oauth_admin()` for admin-only
  views. Legacy mock auth remains in `app/ui/auth.py` for development.

## 3. Domain Services Snapshot
- **Onboarding** (`app/services/onboarding.py`) – validates username/email
  formats, persists onboarding completion, and exposes helper to check status.
- **Request queue** (`app/services/request_service.py`) – creates student badge
  requests, enforces role-based approvals, writes audit records, and updates
  status/reason fields.
- **Roster management** (`app/services/roster_service.py`) – admin/assistant
  operations for listing users, adjusting roles, and creating manual accounts.
- **Catalog management** (`app/services/catalog_service.py`) – CRUD for programs,
  skills, mini-badges, and capstones with extensive validation and audit logging.
- **Progression service** (`app/services/progress_service.py`) – handles awards
  and cascading progression (mini-badge → skill → program) while preventing
  duplicates.
- **Audit service** (`app/services/audit_service.py`) – writes structured audit
  log entries consumed by other services.

## 4. Data Model
Key SQLModel tables (see `app/models/`):
- `users` – core identity, role (admin/assistant/student), onboarding metadata
- `requests` – badge approval workflow, linked to users and (future) badges
- `programs` / `skills` / `mini_badges` / `capstones` – hierarchical catalog
- `awards` – awarded achievements, referencing mini-badges/skills/programs
- `audit_logs` – structured event tracking for privileged operations

Alembic migrations live in `alembic/versions`. Run `alembic upgrade head` to keep
schemas in sync during deployments.

## 5. Logging & Observability
- `app/core/logging.setup_logging()` configures structlog with JSON output in
  production and console output in debug.
- Services generate structured logs for authentication events, onboarding,
  catalog changes, and award operations. The new secrets bootstrap logs missing
  keys to help diagnose misconfiguration on Render.
- Health check: `/?health` returns `{"status": "healthy", "version": "0.3.0", "phase": "3"}`.

## 6. Testing Strategy
- **Unit tests** – `tests/unit/` cover logging setup, config loading, onboarding
  validation, auth service, session manager, catalog/progress services, etc.
- **Integration tests** – `tests/integration/` spin up an in-memory database to
  test end-to-end flows (OAuth sync, onboarding, requests, catalog, progression).
- **Smoke tests** – `tests/test_smoke.py` ensures the Streamlit entry point loads.

Command reference:
```bash
uv run pytest                     # full suite
uv run pytest tests/unit/         # quick unit cycle
uv run pytest tests/integration/  # DB-backed integration tests
```

> Note: Running the suite locally requires dependencies from `requirements.txt`
> (`sqlmodel`, `Authlib`, `structlog`, etc.). Install via `uv sync --extra dev`.

## 7. Deployment & Operations
- Render Blueprint (`render.yaml`) provisions a Postgres database and Streamlit
  web service. Start command runs migrations before launching the app.
- Secrets are supplied via `STREAMLIT_AUTH__*` env vars. The login UI warns when
  keys are missing.
- `RENDER_SECRETS_SETUP.md` and `docs/render_deployment_notes.md` detail the
  manual steps for configuring environment variables and verifying deployments.
- Scripts under `scripts/` (e.g., `seed_catalog.py`) can be run through Render
  Shell for maintenance tasks.

## 8. Known Gaps & Upcoming Work
- **Exports & PII redaction** – planned for Phase 8; current code documents the
  requirement but implementation is pending.
- **Notifications & surfaced audit log UI** – slated for Phase 7.
- **Automated tests in CI** – ensure pipeline installs `sqlmodel` and other deps
  so the existing integration tests run in automation.
- **Configuration hardening** – consider secrets rotation tooling and tighter
  logging sanitization before launch.

## 9. Quick Reference
- Run locally: `uv run streamlit run streamlit_app.py`
- Database migrations: `uv run alembic upgrade head`
- Format & lint: `uv run ruff format . && uv run ruff check .`
- Type check: `uv run mypy app/`
- Bootstrap secrets manually: `uv run python -c "from app.core.secrets_bootstrap import ensure_streamlit_secrets_file; ensure_streamlit_secrets_file()"`

This overview should give new contributors and operators a map of the current
system before tackling the remaining roadmap items.
