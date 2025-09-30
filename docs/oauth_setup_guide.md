# Google OAuth Setup Guide

This guide walks through setting up Google OAuth authentication for the AIPPRO Badging System using Streamlit's native authentication capabilities.

## Prerequisites

- Streamlit 1.42.0 or higher
- Authlib 1.3.2 or higher  
- Google Cloud Console access
- Domain for production deployment (optional for local development)

## Phase 2B Implementation Overview

Phase 2B implements real Google OAuth using Streamlit's native `st.login()` and `st.user` functionality, replacing the mock authentication system from Phase 2A while maintaining backward compatibility.

### Key Features

- **Native Streamlit OAuth**: Uses `st.login()` and `st.user` for authentication
- **User Synchronization**: Syncs OAuth data with existing user database
- **Role Management**: Maintains admin bootstrap via ADMIN_EMAILS
- **Backward Compatibility**: Mock authentication still available for development
- **Session Management**: Leverages Streamlit's built-in session handling

## Google Cloud Console Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your Project ID for later reference

### Step 2: Enable Required APIs

1. Navigate to **APIs & Services** > **Library**
2. Search for and enable:
   - **Google+ API** (if available, though deprecated)
   - **Identity and Access Management (IAM) API**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type (or **Internal** if using Google Workspace)
3. Fill in required information:
   - **App name**: "AIPPRO Badging System"
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
   - **Authorized domains**: Add your deployment domain (use `example.com` for local development)

4. **Scopes**: Add the following scopes:
   - `openid`
   - `email`
   - `profile`

5. **Test users** (if using External type):
   - Add email addresses of users who can test the app
   - This is required while the app is in "Testing" status

### Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client ID**
3. Choose **Web application** as the application type
4. Configure the following:
   - **Name**: "AIPPRO Badging System Web Client"
   - **Authorized redirect URIs**:
     - Local development: `http://localhost:8501/oauth2callback`
     - Production: `https://your-domain.com/oauth2callback`

5. Click **Create** and note down:
   - **Client ID** (ends with `.apps.googleusercontent.com`)
   - **Client Secret** (keep this secure!)

## Application Configuration

### Step 1: Install Dependencies

Ensure you have the correct dependencies installed:

```bash
# Install or upgrade Streamlit and Authlib
uv add "streamlit>=1.42.0" "Authlib>=1.3.2"

# Or if using pip
pip install "streamlit>=1.42.0" "Authlib>=1.3.2"
```

### Step 2: Configure Streamlit Secrets

Create or update `.streamlit/secrets.toml`:

```toml
# OAuth Configuration for Google Authentication
[auth]
# Redirect URI for your environment
redirect_uri = "http://localhost:8501/oauth2callback"  # Local development
# redirect_uri = "https://your-domain.com/oauth2callback"  # Production

# 32-character secret key for cookie signing
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
cookie_secret = "your_32_character_secret_key_here"

# Google OAuth 2.0 credentials from Google Cloud Console
client_id = "your_google_client_id.apps.googleusercontent.com"
client_secret = "your_google_client_secret"

# Google OIDC metadata URL (usually don't change this)
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

# Application Configuration
[general]
debug = true                    # Enable debug mode
enable_mock_auth = true         # Enable mock auth toggle in development
app_env = "development"         # Environment: development, staging, production
```

### Step 3: Environment Variables (Optional)

You can also configure via environment variables in `.env`:

```bash
# Admin Configuration
ADMIN_EMAILS="admin@example.com,admin2@example.com"

# Database Configuration  
DATABASE_URL="sqlite:///./badging_system.db"

# Google OAuth (if not using secrets.toml)
GOOGLE_CLIENT_ID="your_google_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your_google_client_secret"
```

### Step 4: Generate Cookie Secret

Generate a secure cookie secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output to your `cookie_secret` in `secrets.toml`.

## Application Testing

### Step 1: Start the Application

```bash
# Run the application
uv run streamlit run app/main.py

# Or with specific port
uv run streamlit run app/main.py --server.port 8501
```

### Step 2: Test Authentication

1. **Access the application**: Open `http://localhost:8501`
2. **Sign in**: Click "🚀 Sign in with Google"
3. **OAuth flow**: You'll be redirected to Google for authentication
4. **Consent**: Grant permissions to the application
5. **Return**: You'll be redirected back to the application
6. **Success**: You should see your user information and role

### Step 3: Test Admin Access

1. **Configure admin**: Ensure your email is in `ADMIN_EMAILS`
2. **Sign in**: Complete OAuth flow with admin email
3. **Verify role**: Check that you have "🔑 You have administrator privileges"

### Step 4: Test Mock Authentication (Development)

If `enable_mock_auth = true` in secrets:

1. **Access mock auth**: Click "🧪 Mock OAuth" button
2. **Enter details**: Use any email (admin@example.com for admin role)
3. **Sign in**: Click "🔑 Mock Sign In"
4. **Verify**: Check that mock authentication works correctly

## Troubleshooting

### Common Issues

**1. "OAuth not available" error**
- **Cause**: Streamlit version < 1.42.0 or Authlib not installed
- **Solution**: Upgrade dependencies: `uv add "streamlit>=1.42.0" "Authlib>=1.3.2"`

**2. "Invalid redirect URI" error**
- **Cause**: Redirect URI mismatch between Google Console and secrets.toml
- **Solution**: Ensure URLs match exactly (including protocol and port)

**3. "Client ID not found" error**
- **Cause**: Incorrect client_id in configuration
- **Solution**: Verify client_id from Google Cloud Console credentials

**4. Cookie/Session errors**
- **Cause**: Invalid or missing cookie_secret
- **Solution**: Generate new 32-character secret with provided command

**5. "Access blocked" during OAuth**
- **Cause**: App in testing mode and user not added to test users
- **Solution**: Add user email to test users in OAuth consent screen

### Debug Mode

Enable debug mode in `secrets.toml`:

```toml
[general]
debug = true
```

This will show:
- Current authentication method
- OAuth availability status
- Streamlit version information
- OAuth user data (in sidebar expander)

### Production Deployment

For production deployment:

1. **Update redirect URI**: Change to your production domain
2. **Disable debug**: Set `debug = false`
3. **Secure secrets**: Use environment variables or secure secret storage
4. **Publish OAuth app**: Move from "Testing" to "Published" status
5. **Domain verification**: Verify your domain in Google Console

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ st.login()      │───▶│ OAuthSyncService │───▶│ User Database   │
│ (Streamlit)     │    │ (Phase 2B)       │    │ (Phase 2A)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ st.user         │    │ Role Assignment  │    │ Session State   │
│ (OAuth Data)    │    │ & Admin Check    │    │ Management      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Components

- **st.login()**: Streamlit native OAuth initiation
- **st.user**: OAuth user data from Google
- **OAuthSyncService**: Bridges st.user with application database
- **User Database**: Existing SQLModel user management
- **Role Assignment**: Admin bootstrap via ADMIN_EMAILS

### Authentication Flow

1. User clicks "Sign in with Google"
2. Streamlit initiates OAuth flow with Google
3. User authenticates and grants permissions
4. Google redirects back with OAuth data
5. Streamlit populates `st.user` with user information
6. `OAuthSyncService` syncs data with user database
7. Application loads with authenticated user

## Security Considerations

### Best Practices

1. **Secure Secrets**: Never commit secrets to version control
2. **HTTPS in Production**: Always use HTTPS for production OAuth
3. **Domain Verification**: Verify domains in Google Console
4. **Scope Minimization**: Only request necessary OAuth scopes
5. **Session Security**: Rely on Streamlit's secure session handling

### Environment-Specific Configuration

**Development**:
- Use `localhost` redirect URIs
- Enable debug mode
- Use mock authentication for testing

**Staging**:
- Use staging domain redirect URIs
- Disable debug mode
- Use real OAuth only

**Production**:
- Use production domain redirect URIs
- Disable debug and mock authentication
- Use environment variables for secrets
- Enable proper logging and monitoring

## Migration from Phase 2A

Phase 2B maintains backward compatibility with Phase 2A:

- **Existing users**: Will continue to work
- **Mock authentication**: Still available in development
- **Database schema**: No changes required
- **API compatibility**: All existing user management APIs preserved

### Gradual Migration

1. **Deploy Phase 2B**: OAuth available alongside mock auth
2. **Test OAuth**: Verify OAuth works with test users
3. **User migration**: Users can start using OAuth
4. **Disable mock**: Set `enable_mock_auth = false` when ready

## Support and Resources

- **Streamlit Authentication Docs**: https://docs.streamlit.io/develop/tutorials/authentication
- **Google OAuth 2.0 Docs**: https://developers.google.com/identity/protocols/oauth2
- **OIDC Specification**: https://openid.net/connect/
- **Issue Tracking**: Report issues in the project repository

## Next Steps

After OAuth setup is complete:

- **Phase 2C**: Enhanced security features
- **Phase 3**: Badge definitions and criteria  
- **Phase 4**: Badge approval workflows
- **Phase 5**: Student self-service portal