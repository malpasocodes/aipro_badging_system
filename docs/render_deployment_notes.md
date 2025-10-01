# Render Deployment Notes for AIPPRO Badging System

This document summarizes recommendations and clarifications for deploying the AIPPRO Badging System on Render using the provided `render.yaml`.

---

## Key Changes and Recommendations

### 1. Use `env: python` Instead of `runtime: python`
Render's Blueprint spec expects `env: python`. Example:
```yaml
- type: web
  name: aippro-badging-system
  env: python
```

### 2. Pin Python via `runtime.txt`
Instead of relying on an environment variable, create a `runtime.txt` file at the repository root:
```
python-3.11.9
```

This ensures Render selects the correct Python version.

### 3. Database Migrations
Currently the `startCommand` only runs Streamlit. If Alembic migrations are required, prepend them:
```yaml
startCommand: bash -lc "alembic upgrade head && streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true"
```

### 4. Health Check
The current setting:
```
healthCheckPath: /_stcore/health
```
is correct for Streamlit. Keep it.

### 5. Secret Files for Google OAuth
Use Render's **Secret Files** feature to provide `.streamlit/secrets.toml` with the following keys:
```toml
[auth]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"
cookie_secret = "long-random-secret"
redirect_uri = "https://aipro-badging-system.onrender.com/oauth2callback"
```

Make sure this path matches your app code. The redirect URI must exactly match what you register in the Google Cloud Console.

### 6. Environment Variables
Keep environment variables minimal in `render.yaml` and mark sensitive ones with `sync: false` to be set manually in the Render dashboard.

Suggested:
```yaml
envVars:
  - key: APP_ENV
    value: production
  - key: DEBUG
    value: "false"
  - key: LOG_LEVEL
    value: INFO
  - key: DATABASE_URL
    fromDatabase:
      name: aippro-badging-db
      property: connectionString
  - key: ADMIN_EMAILS
    sync: false
  - key: GOOGLE_CLIENT_ID
    sync: false
  - key: GOOGLE_CLIENT_SECRET
    sync: false
```

### 7. Region Consistency
Both the web service and database are set to `oregon`. Keep them aligned.

### 8. Continuous Deployment
Enable automatic deploys from the `main` branch by adding:
```yaml
autoDeploy: true
```

---

## Example Updated `render.yaml`

```yaml
services:
  - type: web
    name: aippro-badging-system
    env: python
    plan: free
    region: oregon
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: bash -lc "alembic upgrade head && streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0 --server.headless true"
    healthCheckPath: /_stcore/health
    autoDeploy: true

    envVars:
      - key: APP_ENV
        value: production
      - key: DEBUG
        value: "false"
      - key: LOG_LEVEL
        value: INFO
      - key: DATABASE_URL
        fromDatabase:
          name: aippro-badging-db
          property: connectionString
      - key: ADMIN_EMAILS
        sync: false
      - key: GOOGLE_CLIENT_ID
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false

databases:
  - name: aippro-badging-db
    databaseName: aippro_badging_system
    plan: free
    region: oregon
    ipAllowList: []
```

---

## Deployment Checklist

1. Add `runtime.txt` with `python-3.11.9`.
2. Push updated `render.yaml` to repo root.
3. Create `.streamlit/secrets.toml` as a Secret File in Render with production values.
4. Update Google Cloud Console OAuth redirect URI:
   - `https://aipro-badging-system.onrender.com/oauth2callback`
5. Add `ADMIN_EMAILS`, `GOOGLE_CLIENT_ID`, and `GOOGLE_CLIENT_SECRET` in the Render Dashboard.
6. Deploy. On first deploy, Alembic migrations will run automatically if configured.
