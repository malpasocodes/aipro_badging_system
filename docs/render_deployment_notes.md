# Render Deployment Notes for AIPPRO Badging System

This document captures the current guidance for deploying the Streamlit app on
Render using the repository’s `render.yaml` Blueprint.

---

## Blueprint Highlights
- **env:** `python`
- **runtime:** pinned via `runtime.txt`
- **buildCommand:** `pip install -r requirements.txt`
- **startCommand:** `alembic upgrade head && streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
- **autoDeploy:** enabled on `main`
- **healthCheckPath:** `/_stcore/health`
- **database:** managed Postgres instance provisioned automatically

## Secrets & Configuration
Render cannot mount `.streamlit/secrets.toml` via Secret Files (forward slashes
are disallowed). Instead set environment variables using Streamlit’s
`STREAMLIT_SECTION__KEY` convention. At runtime
`app/core/secrets_bootstrap.ensure_streamlit_secrets_file()` writes the TOML file
that Streamlit expects.

Recommended variables:

| Key | Value / Source |
| --- | --- |
| `STREAMLIT_AUTH__CLIENT_ID` | Google OAuth client ID |
| `STREAMLIT_AUTH__CLIENT_SECRET` | Google OAuth client secret |
| `STREAMLIT_AUTH__COOKIE_SECRET` | Random 32+ char string (`python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `STREAMLIT_AUTH__REDIRECT_URI` | `https://aipro-badging-system.onrender.com/oauth2callback` |
| `STREAMLIT_AUTH__SERVER_METADATA_URL` | `https://accounts.google.com/.well-known/openid-configuration` |
| `STREAMLIT_GENERAL__DEBUG` | `false` (optional) |
| `STREAMLIT_GENERAL__ENABLE_MOCK_AUTH` | `false` (optional) |
| `ADMIN_EMAILS` | Comma-separated admin list |
| `DATABASE_URL` | Auto-populated from the managed database |

> The bootstrapper also accepts legacy names (`STREAMLIT_AUTH_CLIENT_ID`, etc.)
> but use the double underscores to stay consistent with Streamlit’s mapping.

## Deployment Checklist
1. **Repository**
   - Ensure `render.yaml`, `requirements.txt`, and `runtime.txt` are committed
   - Push latest code to the `main` branch
2. **Render Setup**
   - “New +” → **Blueprint** → select the repo
   - Accept detected services/database from `render.yaml`
3. **Environment Variables**
   - Add `STREAMLIT_AUTH__*`, `STREAMLIT_GENERAL__*`, `ADMIN_EMAILS`
   - Render fills `DATABASE_URL` automatically after the first deploy
4. **Google OAuth Console**
   - Add redirect URI `https://aipro-badging-system.onrender.com/oauth2callback`
   - Verify authorized domain matches the Render URL
5. **Deploy**
   - Trigger **Manual Deploy → Deploy latest commit** if an automatic deploy
     was paused waiting for secrets
   - Watch logs for successful Alembic migrations and Streamlit start-up
6. **Post-Deploy Checks**
   - Visit the public URL; the login card should display the Google sign-in
   - Confirm the health endpoint `/_stcore/health` returns 200
   - (Optional) seed demo data via Render Shell: `python scripts/seed_catalog.py`

## Troubleshooting
- **Missing secrets warning in UI** – Double-check the environment variable
  names, especially the double underscores
- **Alembic migration errors** – Run the same command locally to reproduce,
  fix the migration, push again
- **OAuth redirect mismatch** – Ensure the Render primary URL matches the
  redirect configured in Google Cloud Console
- **Users not granted admin** – Verify `ADMIN_EMAILS` aligns with Google account
  emails (case-insensitive)

## References
- `render.yaml`
- `RENDER_SECRETS_SETUP.md`
- `docs/oauth_setup_guide.md`
- Streamlit secrets documentation: https://docs.streamlit.io/develop/concepts/connections/secrets-management
