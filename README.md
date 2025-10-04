# AIPPRO Badging System

A Streamlit application for managing the AIPPRO badge program. The platform handles Google-based authentication, user onboarding, badge catalog management, approval workflows, and automated progression awards across programs, skills, and mini-badges.

## Features & Current Status
- ✅ **Phase 1** – Project scaffolding, CI, quality toolchain
- ✅ **Phase 2A** – Mock Google auth, session manager, admin bootstrap
- ✅ **Phase 2B** – Native Streamlit OAuth (`st.login`) with database sync, mock fallback
- ✅ **Phase 3** – User onboarding flow with validation and consent capture
- ✅ **Phase 4** – Request queue, roster management, audit logging, role enforcement
- ✅ **Phase 5** – Badge catalog hierarchy (program → skill → mini-badge → capstone)
- ✅ **Phase 6** – Award & progression service (mini-badge → skill → program)
- 🔜 **Phase 7-10** – Notifications, exports with PII redaction, UX polish, launch

## Architecture Snapshot
- **UI Layer** (`app/ui/`, `app/routers/`) – Streamlit views, dialogs, and dashboards per role
- **Services Layer** (`app/services/`) – Auth, onboarding, roster, request queue, catalog, progress, audit
- **Data Model** (`app/models/`) – SQLModel entities for users, requests, programs, skills, badges, awards, audit logs
- **Core Utilities** (`app/core/`) – Configuration, logging, secrets bootstrap, database helpers, session utilities
- **Entry Points** – `streamlit_app.py` (deployment) imports `app.main.main` for orchestration

See `docs/architecture_overview.md` for a full walkthrough of components and data flow.

## Project Structure
```
app/
  core/        # configuration, logging, secrets bootstrap, DB helpers
  ui/          # Streamlit UI components and dialogs
  routers/     # dashboards for admin / assistant / student roles
  services/    # domain services (auth, onboarding, catalog, progress, etc.)
  models/      # SQLModel ORM definitions for the badge domain
alembic/       # database migrations
scripts/       # maintenance and seed scripts
streamlit_app.py  # Render entry point that calls app.main.main
```

## Local Development Setup
1. **Install prerequisites**
   - Python 3.11+
   - [uv](https://github.com/astral-sh/uv)

2. **Install dependencies**
   ```bash
   uv sync --extra dev
   ```

3. **Create environment file**
   ```bash
   cp .env.example .env
   # Update DATABASE_URL (defaults to SQLite) and ADMIN_EMAILS
   ```

4. **Provision secrets**
   - For local work you can keep `.streamlit/secrets.toml` (sample included).
   - In containerized or cloud environments set environment variables using the
     double-underscore convention:
     `STREAMLIT_AUTH__CLIENT_ID`, `STREAMLIT_AUTH__CLIENT_SECRET`,
     `STREAMLIT_AUTH__COOKIE_SECRET`, `STREAMLIT_AUTH__REDIRECT_URI`,
     `STREAMLIT_AUTH__SERVER_METADATA_URL`.
   - `app/core/secrets_bootstrap.ensure_streamlit_secrets_file()` writes
     `.streamlit/secrets.toml` at runtime if those env vars are present.

5. **Initialize the database**
   ```bash
   uv run alembic upgrade head
   ```

6. **Run the app**
   ```bash
   uv run streamlit run streamlit_app.py
   ```
   The UI is available at http://localhost:8501.

## Configuration Reference
- `.env`
  - `DATABASE_URL` – e.g. `sqlite:///./badging_system.db` or Postgres URL
  - `ADMIN_EMAILS` – comma-separated list that bootstrap admin role assignment
  - `LOG_LEVEL`, `DEBUG`, other optional overrides via `Settings`
- `.streamlit/secrets.toml` or `STREAMLIT_AUTH__*` env vars – Google OAuth
  credentials and Streamlit auth settings
- `.streamlit/config.toml` – Streamlit server options (headless, CORS, theme)

## Testing & Quality
```bash
uv run pytest                         # full suite (unit + integration)
uv run pytest tests/unit/             # unit tests only
uv run pytest tests/integration/      # integration tests (requires SQLModel deps)
uv run ruff check . && uv run ruff format .   # lint & format
uv run mypy app/                      # type checking
```
> The provided test suite exercises authentication, onboarding, catalog, request
> workflows, progression logic, and logging. Ensure dependencies like
> `sqlmodel` are installed before running tests.

## Deployment Overview
- `render.yaml` defines the Render Blueprint: Postgres database plus Streamlit web service
- Build command: `pip install -r requirements.txt`
- Start command: `alembic upgrade head && streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
- Configure secrets via environment variables (`STREAMLIT_AUTH__*`) in Render; the
  app bootstraps `.streamlit/secrets.toml` automatically on startup
- Detailed guidance: `DEPLOYMENT.md`, `docs/render_deployment_notes.md`,
  `RENDER_SECRETS_SETUP.md`

## Documentation
- `docs/architecture_overview.md` – codebase evaluation and component guide
- `docs/oauth_setup_guide.md` – Google OAuth configuration
- `docs/render_deployment_notes.md` – Render-specific deployment checklist
- `docs/plans/` – phased implementation plans
- `docs/logs/` – accepted phase outcomes and retrospectives

## Health Check
A lightweight JSON health check is exposed by visiting `/?health`:
```json
{"status": "healthy", "version": "0.3.0", "phase": "3"}
```

## Roadmap
1. Notifications & audit surfacing
2. Export workflows with PII redaction
3. UX polish & accessibility
4. Launch hardening (monitoring, backups, custom domain)

## Maintainer
- Alfred Essa (@malpasocodes)
