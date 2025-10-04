# Render Deployment (Clean Setup)

This guide walks through provisioning a brand-new Render deployment for the AIPPRO Badging System after deleting any previous services. Follow the steps in order; each builds on the previous one.

## Audience & Prerequisites

You should be comfortable with Git, Python tooling, and the Render dashboard. Before you begin, make sure you have:

- A GitHub repository containing this project (`main` branch recommended).
- A Render account with permission to create Blueprint services and PostgreSQL databases.
- Google OAuth credentials (Client ID + Client Secret) for the production domain.
- A terminal with `uv` (preferred) or `pip`, plus access to run `git` commands.
- Ability to generate a 32-character secret (`python -c "import secrets; print(secrets.token_urlsafe(32))"`).

> **Tip:** If you removed the prior Render service, you must recreate both the web app and the database in one pass. Render's Blueprint flow handles this automatically when the repository root contains `render.yaml`.

---

## 1. Prepare the Repository

1. **Sync dependencies locally** so `requirements.txt` and `uv.lock` are fresh:
   ```bash
   uv sync
   ```
2. **Regenerate `requirements.txt`** if packages changed:
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   ```
3. Confirm the deployment files exist and are committed:
   - `render.yaml` (Blueprint definition)
   - `requirements.txt`
   - `runtime.txt` (pins Python 3.11 for Render)
4. Run and review tests as needed, then push the latest `main` branch so Render builds from the correct commit:
   ```bash
   git push origin main
   ```

> The Blueprint will execute the `buildCommand` and `startCommand` defined in `render.yaml`. Verify the file before pushing if you made local modifications.

---

## 2. Create a New Blueprint Deployment on Render

1. Sign in to [Render](https://dashboard.render.com/) and click **New → Blueprint**.
2. Choose the GitHub repository for the AIPPRO Badging System.
3. Render detects `render.yaml` automatically and shows a summary:
   - **Web Service**: `aippro-badging-system` (Python, Free plan by default)
   - **Database**: `aippro-badging-db` (PostgreSQL, Free plan)
4. Click **Apply** to create both resources. Render immediately provisions the database and queues the first build for the web service.

> If you deleted the previous service name, you can reuse it. Otherwise, edit the service name in the preview (and optionally in `render.yaml`) before clicking **Apply**.

---

## 3. Supply Required Environment Secrets

The Blueprint cannot ship OAuth secrets. Before the first build finishes, add these variables manually:

1. Open the newly created service → **Environment → Environment Variables**.
2. Add or edit the keys below (Render stores them encrypted). Use **double underscores** to separate the section from the key—Streamlit maps `STREAMLIT_AUTH__CLIENT_ID` to `st.secrets["auth"]["client_id"]`. The app also accepts the legacy single underscore names, but the double underscore form avoids ambiguity.

| Key | Example Value | Notes |
| --- | --- | --- |
| `STREAMLIT_AUTH__CLIENT_ID` | `your-client-id.apps.googleusercontent.com` | Google OAuth Client ID |
| `STREAMLIT_AUTH__CLIENT_SECRET` | `your-google-client-secret` | Google OAuth Client Secret |
| `STREAMLIT_AUTH__COOKIE_SECRET` | output of `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Required for secure cookies |
| `STREAMLIT_AUTH__REDIRECT_URI` | `https://<service-name>.onrender.com/oauth2callback` | Must match Google console redirect URI |
| `STREAMLIT_AUTH__SERVER_METADATA_URL` | `https://accounts.google.com/.well-known/openid-configuration` | Google OIDC metadata endpoint |
| `STREAMLIT_GENERAL__DEBUG` | `false` | Disable verbose debug UI in production |
| `STREAMLIT_GENERAL__ENABLE_MOCK_AUTH` | `false` | Blocks mock auth in production |
| `ADMIN_EMAILS` | `admin1@example.com,admin2@example.com` | Comma-separated list of allowed admin accounts |

3. Save the environment variable changes. The next build (or a manual redeploy) will include them.

> At startup the app calls `ensure_streamlit_secrets_file()` to write `.streamlit/secrets.toml` from these variables. If any required key is missing, the login screen lists which ones to supply and the logs emit a `Streamlit OAuth configuration missing required secrets` warning. `render.yaml` marks the keys with `sync: false` so you remember to set them in the dashboard.

---

## 4. Configure Google OAuth

1. Visit [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials).
2. Open your OAuth 2.0 Client ID and add the following:
   - **Authorized redirect URI**: `https://<service-name>.onrender.com/oauth2callback`
   - **Authorized JavaScript origin**: `https://<service-name>.onrender.com`
3. Save changes. If you changed the service name, update the URIs accordingly.
4. (Optional) Restrict the OAuth consent screen to the admin email domain for tighter control.

> Complete this step before attempting to sign in on Render; otherwise Google will block the callback and your users will be stuck at the login screen.

---

## 5. Understand the Build & Start Commands

Render executes the commands from `render.yaml` every deploy:

- **Build command**
  ```bash
  pip install -r requirements.txt
  ```
  Installs the project into the managed virtual environment.

- **Start command**
  ```bash
  alembic upgrade head && streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
  ```
  Runs database migrations first, then launches Streamlit from the root-level `streamlit_app.py` entry point (which imports `app.main`).

> If Alembic fails, Render never starts Streamlit and logs will show the stack trace. Fix the migration issue locally, push a new commit, then deploy again.

---

## 6. First Deploy & Verification Checklist

1. **Trigger the initial build** if Render paused waiting for secrets: click **Manual Deploy → Deploy latest commit** after setting environment variables.
2. **Watch the Logs tab** for these milestones:
   - Dependency installation completes without errors.
   - `alembic upgrade head` logs each migration ID.
   - Streamlit reports `You can now view your Streamlit app`.
3. Once the service reports “Live”, open the URL. You should see the sign-in card with a Google sign-in button (no missing-secret warning). The logs should contain a `Bootstrapped Streamlit secrets file` entry on successful startup.
4. **Sign in with a Google account listed in `ADMIN_EMAILS`**. On first login you may be prompted to complete onboarding in-app.
5. Confirm the admin dashboard renders and no tracebacks appear in the logs.

> If you need fresh sample catalog data, open Render Shell (service → **Shell**) and run:
> ```bash
> cd /opt/render/project/src
> python scripts/seed_catalog.py
> ```
> The script skips seeding automatically if data already exists.

---

## 7. Ongoing Operations

- **Manual redeploy**: Use **Manual Deploy → Deploy latest commit** after pushing to `main`.
- **Clear build cache**: If dependency changes don’t stick, choose **Manual Deploy → Deploy latest commit (Clear build cache)**.
- **Rotate secrets**: Update the relevant environment variable and redeploy. For cookie secret rotation, users are signed out automatically.
- **Run ad-hoc commands**: Use Render Shell. Example for Alembic downgrade:
  ```bash
  cd /opt/render/project/src
  alembic downgrade -1
  ```
- **Database access**: View credentials under the database resource; use `psql` locally or managed backups for exports.

---

## Troubleshooting Quick Reference

- **`StreamlitAuthError` on sign-in**: One or more `STREAMLIT_AUTH_*` variables missing or typo’d; revisit Section 3.
- **`ModuleNotFoundError: app`**: Ensure the start command runs `streamlit_app.py` (already configured) or that the repo root contains the `app` package.
- **Alembic migration failures**: Run the same command locally (`alembic upgrade head`) and fix before redeploying.
- **Google OAuth redirect mismatch**: Update the URI in Google Cloud Console to match the exact Render domain.

With these steps your Render deployment starts cleanly and stays reproducible: the Blueprint defines infrastructure, environment variables provide secrets, and migrations run on every start to keep the database schema current.

For more context, see `docs/render_deployment_notes.md` (Blueprint deep dive), `RENDER_SECRETS_SETUP.md` (environment-variable mapping), and `docs/oauth_setup_guide.md` (Google Console configuration).
