# Render Secrets Configuration

Streamlit now reads OAuth secrets from either `.streamlit/secrets.toml` **or**
`STREAMLIT_*` environment variables. On Render we rely on environment variables
because Secret Files do not allow nested paths. At runtime the app creates
`.streamlit/secrets.toml` automatically from those variables via
`app/core/secrets_bootstrap.ensure_streamlit_secrets_file()`.

## Required Environment Variables
Set the following under **Environment → Environment Variables**. The double
underscore separates the section (`auth`) from the key.

| Key | Example Value | Notes |
| --- | --- | --- |
| `STREAMLIT_AUTH__CLIENT_ID` | `your-client-id.apps.googleusercontent.com` | Google OAuth client ID |
| `STREAMLIT_AUTH__CLIENT_SECRET` | `xxxxxxxx` | Google OAuth client secret |
| `STREAMLIT_AUTH__COOKIE_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | 32+ character signing secret |
| `STREAMLIT_AUTH__REDIRECT_URI` | `https://aipro-badging-system.onrender.com/oauth2callback` | Must match Google console |
| `STREAMLIT_AUTH__SERVER_METADATA_URL` | `https://accounts.google.com/.well-known/openid-configuration` | Default Google OIDC metadata |
| `STREAMLIT_GENERAL__DEBUG` | `false` | Optional: toggle debug mode |
| `STREAMLIT_GENERAL__ENABLE_MOCK_AUTH` | `false` | Optional: disable mock auth in prod |

> Legacy single-underscore names (`STREAMLIT_AUTH_CLIENT_ID`, etc.) are still
> read as a fallback by the bootstrapper, but prefer the double-underscore
> convention to match Streamlit’s documented mapping.

## Verification
After saving the variables:

1. Trigger **Manual Deploy → Deploy latest commit**.
2. Check deploy logs for `Bootstrapped Streamlit secrets file` – this confirms
   the runtime file was generated.
3. (Optional) Open a Render Shell and run:
   ```bash
   cd /opt/render/project/src
   python - <<'PY'
   import tomllib
   from pathlib import Path
   secrets = tomllib.loads(Path('.streamlit/secrets.toml').read_text())
   print(secrets['auth'].keys())
   PY
   ```
   You should see the five auth keys listed.

If any keys are missing the login page will display which items are absent and
Log Stream will contain a warning from `app.ui.oauth_auth`.

## Helpful References
- `docs/render_deployment_notes.md`
- `docs/oauth_setup_guide.md`
- Streamlit secrets docs: https://docs.streamlit.io/develop/concepts/connections/secrets-management
