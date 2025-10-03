# Render Secrets Configuration Workaround

## Problem
Render's Secret Files feature doesn't allow forward slashes in filenames, so `.streamlit/secrets.toml` won't work.

## Solution
Use **Streamlit's environment variable support** for secrets instead.

Streamlit automatically reads secrets from environment variables prefixed with `STREAMLIT_`.

## Steps for Render Dashboard

### In Render Dashboard → Environment → Environment Variables

Add these variables (in addition to the ones already configured):

| Key | Value | Notes |
|-----|-------|-------|
| `STREAMLIT_AUTH_CLIENT_ID` | `YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com` | Your Google OAuth Client ID |
| `STREAMLIT_AUTH_CLIENT_SECRET` | `YOUR_GOOGLE_CLIENT_SECRET` | Your Google OAuth Client Secret |
| `STREAMLIT_AUTH_COOKIE_SECRET` | `YOUR_32_CHARACTER_SECRET` | New cookie secret for production (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `STREAMLIT_AUTH_REDIRECT_URI` | `https://aippro-badging-system.onrender.com/oauth2callback` | Production redirect URI (update with your actual Render URL) |
| `STREAMLIT_AUTH_SERVER_METADATA_URL` | `https://accounts.google.com/.well-known/openid-configuration` | Google OIDC metadata |
| `STREAMLIT_GENERAL_DEBUG` | `false` | Disable debug mode in production |
| `STREAMLIT_GENERAL_ENABLE_MOCK_AUTH` | `false` | Disable mock auth in production |

## How It Works

Streamlit automatically converts environment variables to secrets:
- `STREAMLIT_AUTH_CLIENT_ID` → `st.secrets["auth"]["client_id"]`
- `STREAMLIT_AUTH_CLIENT_SECRET` → `st.secrets["auth"]["client_secret"]`  
- `STREAMLIT_GENERAL_DEBUG` → `st.secrets["general"]["debug"]`
- etc.

The double underscore `_` separates the section from the key.

## No Code Changes Required!

Your existing code that uses `st.secrets["auth"]["client_id"]` will work automatically - Streamlit reads from environment variables when secrets.toml is not present.

## Reference

Streamlit Documentation: https://docs.streamlit.io/develop/concepts/connections/secrets-management#use-secrets-on-render
