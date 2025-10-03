# Deployment Guide: AIPPRO Badging System on Render

This guide provides step-by-step instructions for deploying the AIPPRO Badging System to Render.com from a GitHub repository.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Setup](#pre-deployment-setup)
3. [Deploy to Render](#deploy-to-render)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Production Checklist](#production-checklist)

---

## Prerequisites

Before deploying, ensure you have:

### 1. GitHub Repository
- ✅ Code pushed to GitHub (main branch)
- ✅ `render.yaml` file in repository root (already present)
- ✅ `requirements.txt` file generated from uv

### 2. Render Account
- Create account at [render.com](https://render.com)
- Free tier is sufficient for initial deployment

### 3. Google OAuth Credentials
- Google Cloud Project created
- OAuth 2.0 Client ID configured
- You'll need:
  - Client ID
  - Client Secret

---

## Pre-Deployment Setup

### Step 1: Generate requirements.txt

Render needs a `requirements.txt` file (doesn't support uv natively):

```bash
# Generate from pyproject.toml
uv pip compile pyproject.toml -o requirements.txt

# Or export from current environment
uv pip freeze > requirements.txt
```

**Commit and push:**
```bash
git add requirements.txt
git commit -m "build: Add requirements.txt for Render deployment"
git push
```

### Step 2: Create runtime.txt (Optional but Recommended)

Pin Python version for Render:

```bash
echo "python-3.11.9" > runtime.txt
git add runtime.txt
git commit -m "build: Add runtime.txt for Render Python version"
git push
```

### Step 3: Prepare Secrets Configuration

You'll need these values for deployment:

1. **Google OAuth Client ID** - From Google Cloud Console
2. **Google OAuth Client Secret** - From Google Cloud Console
3. **Cookie Secret** - Generate new 32-character secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
4. **Admin Emails** - Comma-separated list: `admin1@example.com,admin2@example.com`

---

## Deploy to Render

### Step 1: Connect GitHub Repository

1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account if not already connected
4. Select your repository: `your-username/aipro_badging_system`
5. Render will detect `render.yaml` automatically
6. Click **"Apply"**

Render will create:
- ✅ Web Service: `aippro-badging-system`
- ✅ PostgreSQL Database: `aippro-badging-db`

### Step 2: Configure Secrets via Environment Variables

**IMPORTANT:** Render's Secret Files feature doesn't allow forward slashes in filenames, so we use Streamlit's environment variable support instead.

Streamlit automatically reads secrets from environment variables prefixed with `STREAMLIT_`.

1. Go to your web service: **aippro-badging-system**
2. Navigate to **Environment** → **Environment Variables**
3. Add the following variables (in addition to those in Step 3):

| Key | Value | Notes |
|-----|-------|-------|
| `STREAMLIT_AUTH_CLIENT_ID` | `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com` | Your Google OAuth Client ID |
| `STREAMLIT_AUTH_CLIENT_SECRET` | `YOUR_GOOGLE_CLIENT_SECRET` | Your Google OAuth Client Secret |
| `STREAMLIT_AUTH_COOKIE_SECRET` | `YOUR_32_CHARACTER_SECRET_FROM_STEP_3` | New cookie secret for production |
| `STREAMLIT_AUTH_REDIRECT_URI` | `https://aippro-badging-system.onrender.com/oauth2callback` | Production redirect URI (update with your actual Render URL) |
| `STREAMLIT_AUTH_SERVER_METADATA_URL` | `https://accounts.google.com/.well-known/openid-configuration` | Google OIDC metadata |
| `STREAMLIT_GENERAL_DEBUG` | `false` | Disable debug mode in production |
| `STREAMLIT_GENERAL_ENABLE_MOCK_AUTH` | `false` | Disable mock auth in production |

**How it works:**
- `STREAMLIT_AUTH_CLIENT_ID` → `st.secrets["auth"]["client_id"]`
- `STREAMLIT_AUTH_CLIENT_SECRET` → `st.secrets["auth"]["client_secret"]`
- `STREAMLIT_GENERAL_DEBUG` → `st.secrets["general"]["debug"]`

No code changes required - your existing code using `st.secrets` will work automatically.

**Note:** Replace `aippro-badging-system` with your actual Render service name if different.

For more details, see `RENDER_SECRETS_SETUP.md` in the repository.

### Step 3: Configure Additional Environment Variables

In the Render Dashboard (still in **Environment** → **Environment Variables**), add this additional variable:

| Key | Value | Example |
|-----|-------|---------|
| `ADMIN_EMAILS` | Comma-separated admin emails | `admin@example.com,admin2@example.com` |

**Note:** `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are now configured via `STREAMLIT_AUTH_CLIENT_ID` and `STREAMLIT_AUTH_CLIENT_SECRET` in Step 2.

**Auto-configured variables** (from render.yaml - do not modify):
- `APP_ENV` = `production`
- `DEBUG` = `false`
- `LOG_LEVEL` = `INFO`
- `DATABASE_URL` = (auto-populated from database)

### Step 4: Update Google OAuth Settings

**CRITICAL:** Update your Google Cloud Console OAuth settings:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Select your OAuth 2.0 Client ID
3. Under **Authorized redirect URIs**, add:
   ```
   https://aippro-badging-system.onrender.com/oauth2callback
   ```
   (Replace `aippro-badging-system` with your actual service name)

4. Under **Authorized JavaScript origins**, add:
   ```
   https://aippro-badging-system.onrender.com
   ```

5. Click **"Save"**

### Step 5: Trigger Deployment

If auto-deploy is enabled (default), deployment starts automatically when you applied the blueprint.

Otherwise:
1. Go to your web service dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

**Deployment process:**
1. Render pulls code from GitHub
2. Installs dependencies from `requirements.txt`
3. Runs database migrations: `alembic upgrade head`
4. Starts Streamlit app: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

**Monitor deployment:**
- Watch **Logs** tab for progress
- Deployment typically takes 3-5 minutes

---

## Post-Deployment Configuration

### Step 1: Verify Database Migrations

Check logs for successful migration:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 8b8ce54544c9, create initial users table
INFO  [alembic.runtime.migration] Running upgrade 8b8ce54544c9 -> b82afc5ef86a, add requests table for badge approval workflow
INFO  [alembic.runtime.migration] Running upgrade b82afc5ef86a -> 1723fabe8f8c, add onboarding_completed_at field for phase 3
INFO  [alembic.runtime.migration] Running upgrade 1723fabe8f8c -> 4a5be144caf5, add catalog tables programs skills mini badges and capstones
INFO  [alembic.runtime.migration] Running upgrade 4a5be144caf5 -> 2bfe54925752, add awards table for earned badges
```

### Step 2: Access Your Application

Visit your deployed app:
```
https://aippro-badging-system.onrender.com
```

You should see the Google Sign-In page.

### Step 3: Test OAuth Login

1. Click **"Sign in with Google"**
2. Authenticate with a Google account matching one of your `ADMIN_EMAILS`
3. Complete onboarding form (username, Substack email, Meetup email)
4. You should be redirected to the Admin Dashboard

### Step 4: Seed Initial Data (Optional)

If you want to add sample badge catalog data:

1. Open Render Shell:
   - Go to service dashboard → **Shell** tab
   - Click **"Connect to Shell"**

2. Run seed script:
   ```bash
   python scripts/seed_catalog.py
   ```

---

## Verification

### Health Check

Render automatically monitors: `https://aippro-badging-system.onrender.com/_stcore/health`

Expected response: `200 OK`

### Database Connection

Check logs for:
```
INFO  [app.core.database] Database connection successful
```

### OAuth Authentication

Test login flow:
1. Sign in with admin email
2. Verify admin role assigned
3. Check Admin Dashboard access
4. Test creating a user via User Management

### Key Features

Verify these work:
- ✅ User authentication (Google OAuth)
- ✅ Admin can access all sections
- ✅ Badge catalog displays (if seeded)
- ✅ User roster shows admin user
- ✅ No errors in Render logs

---

## Troubleshooting

### Issue: "OAuth Error - redirect_uri_mismatch"

**Cause:** Redirect URI in Google Console doesn't match deployed URL.

**Fix:**
1. Check exact URL in error message
2. Add it to Google Cloud Console → OAuth Client → Authorized redirect URIs
3. Make sure `.streamlit/secrets.toml` redirect_uri matches exactly

### Issue: "Database connection failed"

**Cause:** DATABASE_URL not set or incorrect.

**Fix:**
1. Verify PostgreSQL database is running (Render Dashboard → Databases)
2. Check Environment variables - `DATABASE_URL` should be auto-populated
3. Restart web service if needed

### Issue: "Secret file not found: .streamlit/secrets.toml"

**Cause:** Render's Secret Files feature doesn't support forward slashes in filenames.

**Fix:**
1. Use environment variables instead (see RENDER_SECRETS_SETUP.md)
2. Add all `STREAMLIT_AUTH_*` and `STREAMLIT_GENERAL_*` variables in Environment → Environment Variables
3. Verify all required variables are set (see Step 2)
4. Redeploy

### Issue: "No module named 'app'"

**Cause:** requirements.txt missing dependencies.

**Fix:**
1. Regenerate requirements.txt:
   ```bash
   uv pip compile pyproject.toml -o requirements.txt
   ```
2. Push to GitHub
3. Render will auto-deploy

### Issue: "Migration failed"

**Cause:** Database schema conflict or migration issue.

**Fix:**
1. Check Render logs for specific Alembic error
2. If starting fresh, can reset database via Render Dashboard
3. Ensure all migrations are in repo under `alembic/versions/`

### Issue: App loads but no admin access

**Cause:** `ADMIN_EMAILS` not set or email doesn't match.

**Fix:**
1. Verify `ADMIN_EMAILS` environment variable is set
2. Ensure email matches exactly (case-sensitive)
3. Try signing out and back in
4. Check logs for "role assignment" messages

---

## Production Checklist

Before going live with real users:

### Security
- [ ] `DEBUG` set to `false`
- [ ] `DATABASE_ECHO` not set (or set to `false`)
- [ ] `ENABLE_MOCK_AUTH` not enabled
- [ ] Cookie secret is strong (32+ characters)
- [ ] Admin emails verified and limited

### Performance
- [ ] Upgrade from free tier if needed (for better uptime)
- [ ] Database on paid plan for backups
- [ ] Monitor response times

### Monitoring
- [ ] Enable Render email alerts
- [ ] Set up uptime monitoring (e.g., UptimeRobot)
- [ ] Review Render logs regularly

### Backups
- [ ] Enable PostgreSQL automatic backups (paid plan)
- [ ] Export badge catalog data periodically
- [ ] Document recovery procedures

### Custom Domain (Optional)
- [ ] Purchase domain
- [ ] Add custom domain in Render Dashboard
- [ ] Update Google OAuth authorized domains
- [ ] Update redirect URIs

### User Management
- [ ] Test student user flow
- [ ] Test assistant user flow
- [ ] Verify badge request workflow
- [ ] Test badge earning and progression

---

## Support

### Render Documentation
- [Blueprint Spec](https://render.com/docs/blueprint-spec)
- [Environment Variables](https://render.com/docs/environment-variables)
- [Secret Files](https://render.com/docs/secret-files)
- [PostgreSQL](https://render.com/docs/databases)

### Project Documentation
- See `docs/oauth_setup_guide.md` for OAuth configuration
- See `docs/plans/` for implementation details
- See `docs/logs/phase_five_outcome.md` for latest features

### Getting Help
- Check Render logs first (most issues show here)
- Verify Google OAuth configuration
- Review `.streamlit/secrets.toml` format
- Check environment variables match expectations

---

## Quick Reference

### Render Service URLs
- **Web Service:** `https://aippro-badging-system.onrender.com`
- **Health Check:** `https://aippro-badging-system.onrender.com/_stcore/health`
- **OAuth Callback:** `https://aippro-badging-system.onrender.com/oauth2callback`

### Required Environment Variables (Set in Render Dashboard)

**Streamlit Secrets (via environment variables):**
- `STREAMLIT_AUTH_CLIENT_ID` - OAuth Client ID
- `STREAMLIT_AUTH_CLIENT_SECRET` - OAuth Client Secret
- `STREAMLIT_AUTH_REDIRECT_URI` - `https://your-app.onrender.com/oauth2callback`
- `STREAMLIT_AUTH_COOKIE_SECRET` - 32-character random string
- `STREAMLIT_AUTH_SERVER_METADATA_URL` - `https://accounts.google.com/.well-known/openid-configuration`
- `STREAMLIT_GENERAL_DEBUG` - `false`
- `STREAMLIT_GENERAL_ENABLE_MOCK_AUTH` - `false`

**Application Configuration:**
- `ADMIN_EMAILS` - Comma-separated admin emails

### Database Connection
Auto-configured via `render.yaml`:
- `DATABASE_URL` - PostgreSQL connection string (auto-populated)

---

**Deployment Status:** Ready for production ✅

**Last Updated:** 2025-10-03 (Phase 5 v0.5.3)
