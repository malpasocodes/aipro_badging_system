# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the AIPPRO Badging System - a Python/Streamlit application for recognizing and tracking student achievement through digital badges. The system supports identity verification, onboarding, role-based approvals, and progression from mini-badges to capstones.

**Tech Stack:** Python 3.11+ • Streamlit • uv (package management) • PostgreSQL • Google Identity Services (OAuth) • Render (deployment)

## Project Structure

This repository contains a working Python/Streamlit application with the following structure:

```
/app
  /core          # config, logging, security, utils
  /ui            # UI helpers, components, theming  
  /models        # pydantic models & ORM schema
  /services      # domain services (auth, onboarding, badges, approvals, exports, audit)
  /dal           # repositories / DB access
  /routers       # page controllers (Home, Badges, Approvals, Admin, Profile)
/docs
  /plans         # Phase planning documents (phase_one_plan.md, etc.)
  /logs          # Phase execution outcome logs
  /specs         # Technical specifications and requirements
/tests           # unit, integration, e2e tests
pyproject.toml   # project configuration
uv.lock          # dependency lockfile
```

## Development Commands

**Current Status:** Phase 2B (Real Google OAuth) is provisionally accepted. The following commands are available:

### Environment Setup
```bash
uv sync --extra dev       # Install dependencies including dev tools
uv sync --frozen          # Install from lockfile (CI/CD)
```

### Development
```bash
# Run the application locally
uv run streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0
# Or simply:
uv run streamlit run app/main.py

# Linting and formatting
uv run ruff check .               # Lint code
uv run ruff check --fix .         # Auto-fix linting issues
uv run ruff format .              # Format code

# Type checking
uv run mypy app/                  # Type check application code

# Testing
uv run pytest                     # Run all tests
uv run pytest tests/unit/         # Run unit tests only
uv run pytest tests/integration/  # Run integration tests
uv run pytest -v                  # Verbose output
uv run pytest -k test_name        # Run specific test by name
uv run pytest -x                  # Stop on first failure
uv run pytest --lf                # Run last failed tests
uv run coverage run -m pytest     # Run tests with coverage
uv run coverage report            # Show coverage report
uv run coverage html              # Generate HTML coverage report
```

### Database Operations
```bash
# Database migrations (Alembic configured)
uv run alembic upgrade head       # Apply migrations
uv run alembic revision --autogenerate -m "message"  # Generate new migration
uv run alembic current            # Show current revision
uv run alembic history            # Show migration history
uv run alembic downgrade -1       # Rollback last migration

# Development database reset (SQLite only)
rm badging_system.db && uv run alembic upgrade head
```

## Architecture Highlights

### Data Model (Current - Phase 2B)
- **users**: Google OAuth integration with roles (admin/student)
  - Fields: id, email, username, google_sub, role, created_at, updated_at, last_login_at
  - Roles: admin (from ADMIN_EMAILS), student (default)
  - OAuth sync via OAuthSyncService

### Future Data Model (Phases 3-8)
- **Badge Hierarchy**: programs → skills → mini_badges → capstones
- **requests**: Badge approval workflow with audit trail
- **awards**: Earned badges with automatic progression logic
- **notifications**: In-app messaging system
- **audit_logs**: Complete audit trail for all privileged operations

### Key Services (Implemented)
- **AuthService** (app/services/auth.py): User management and role assignment
- **OAuthSyncService** (app/services/oauth.py): Streamlit OAuth integration and user synchronization
- **OAuth2MockService** (app/services/oauth.py): Mock OAuth for testing

### Future Services (Phases 3-8)
- **CatalogService**: CRUD operations for badge hierarchy
- **RequestService**: Badge request submission and approval workflow
- **ProgressService**: Automatic award calculation and progression logic
- **ExportService**: PII-compliant data exports for administrators
- **NotificationService**: In-app notifications

### Security & Privacy (Current - Phase 2B)
- Google Identity Services OAuth with Streamlit 1.42+ native authentication
- Role-based access control (RBAC) with admin bootstrap from ADMIN_EMAILS
- Streamlit's built-in secure session management
- SQLite for development, PostgreSQL ready for production

### Future Security & Privacy (Phases 2C-8)
- Enhanced PII redaction for all exports
- Complete audit logging for privileged operations
- CSRF protection and rate limiting

### Future Business Rules (Phases 3-6)
- Badge progression: Program → Skills → Mini-badges (strict DAG)
- Skill awards granted when ALL child mini-badges are approved
- Program awards granted when ALL skills are awarded (+ optional capstone)
- Requests are immutable after decision (new request required for changes)
- No badge expiration in v1

## Deployment Configuration

**Platform:** Render (planned)
- **Web Service:** Streamlit app
- **Database:** SQLite (dev), PostgreSQL (production)
- **Environment Variables:**
  - `DATABASE_URL` - Database connection string
  - `ADMIN_EMAILS` - Comma-separated admin emails
  - `APP_ENV` - Environment: development/staging/production
  - `LOG_LEVEL` - Logging level (INFO, DEBUG, etc.)
  - `DEBUG` - Enable/disable debug mode

**Streamlit Secrets (.streamlit/secrets.toml):**
  - `auth.client_id` - Google OAuth client ID
  - `auth.client_secret` - Google OAuth client secret
  - `auth.redirect_uri` - OAuth callback URL
  - `auth.cookie_secret` - 32-char secret for cookie signing
  - `general.enable_mock_auth` - Enable mock auth toggle (dev only)

**Build Commands:**
- Build: `uv sync --frozen`
- Start: `uv run streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`

## Development Guidelines

### Role-Based Features (Current - Phase 2B)
- **Students**: Default role for all OAuth users
- **Administrators**: Users listed in ADMIN_EMAILS environment variable

### Future Role-Based Features (Phases 3-8)
- **Students**: Request mini-badges, view progress, receive notifications
- **Assistants**: Approve/reject requests, manage roster
- **Administrators**: Full control including catalog management, exports

### UI/UX Patterns (Current)
- Streamlit native OAuth sign-in interface
- Role-aware authentication state
- Mock authentication available in development mode

### Future UI/UX Patterns (Phases 3-9)
- Streamlit sidebar for global navigation
- PII masking in all user interfaces
- Toast notifications for user feedback
- Comprehensive form validation with inline errors

## Phase Planning and Approval Process

**CRITICAL:** Each development phase requires formal planning, approval, and acceptance before proceeding.

### Workflow for Each Phase

1. **Plan Development**
   - Create detailed plan document as `docs/plans/phase_[number]_plan.md` (e.g., `phase_one_plan.md`)
   - Include: objectives, detailed approach, deliverables, acceptance criteria, risks, timeline
   - Plan must be comprehensive and actionable

2. **Alfred Essa Review & Approval**
   - Plan document must be reviewed by Alfred Essa
   - Approval recorded in plan document with timestamp
   - Format: `## APPROVAL\nApproved by: Alfred Essa\nDate: [YYYY-MM-DD HH:MM UTC]\nNotes: [any additional notes]`

3. **Phase Execution**
   - Implementation can only begin after written approval
   - Follow plan exactly or document deviations with rationale
   - Maintain development best practices and testing standards

4. **Alfred Essa Acceptance**
   - Completed phase must be accepted by Alfred Essa
   - Acceptance recorded in plan document with timestamp
   - Format: `## ACCEPTANCE\nAccepted by: Alfred Essa\nDate: [YYYY-MM-DD HH:MM UTC]\nOutcome: [brief summary]\nNotes: [any additional notes]`

5. **Outcome Logging**
   - Brief outcome log created in `docs/logs/phase_[number]_outcome.md`
   - Include: completion date, key achievements, issues encountered, lessons learned

6. **Code Commit Authorization**
   - Code can only be committed after phase acceptance
   - Include phase acceptance reference in commit message

### Plan Document Template
Each phase plan should include:
- **Objectives**: Clear goals for the phase
- **Approach**: Detailed technical approach and methodology
- **Deliverables**: Specific artifacts to be created
- **Acceptance Criteria**: Measurable success criteria
- **Risks**: Potential issues and mitigation strategies
- **Dependencies**: Prerequisites and external dependencies
- **Timeline**: Estimated duration and milestones

## Project Phases

The project is divided into 10 incremental phases, each requiring formal planning and approval:

### Completed Phases
1. ✅ **Project Setup & Repo Initialization** - Complete (Phase 1)
2. ✅ **Authentication & Session Management**
   - Phase 2A: Mock Authentication ✅ Complete
   - Phase 2B: Real Google OAuth ✅ **ACCEPTED**
   - Phase 2C: Enhanced Security (Planned)
3. ✅ **Onboarding Flow** - ✅ **ACCEPTED** (Phase 3)
   - User registration with username, Substack email, Meetup email
   - Role-based routing (Admin/Assistant/Student dashboards)
   - Comprehensive validation and testing (43 tests passing)

### Upcoming Phases
4. Roles & Approvals Queue
5. Badge Data Model & Catalog
6. Earning Logic & Awards
7. Notifications & Audit Trails
8. Exports & PII Redaction
9. UX Polish & Accessibility
10. Deployment & Launch

**Note:** No phase can begin without an approved plan document in `docs/plans/`.

**Phase 2B Status**: ACCEPTED ✅ - Implementation complete, tested (43/43 auth/OAuth tests passing), and verified with real Google OAuth credentials. Ready for production deployment.

**Phase 3 Status**: ACCEPTED ✅ - User onboarding and registration complete with role-based routing. All 43 tests passing (34 unit + 9 integration). Admin role auto-sync implemented. Ready for production deployment.

## Current Authentication & Onboarding System (Phases 2B + 3)

### Implementation Status
- **Real Google OAuth**: Native Streamlit OAuth using st.login() and st.user
- **Backward Compatibility**: Mock authentication still available for development
- **User Synchronization**: OAuth data synced with existing user database
- **Role-Based Access**: Admin/Assistant/Student roles with environment-based bootstrap
- **User Onboarding**: Registration form captures username, Substack email, Meetup email, and consent
- **Role-Based Routing**: Smart routing to Admin/Assistant/Student dashboards based on role and onboarding status
- **Admin Role Sync**: Automatic role updates based on ADMIN_EMAILS list on every login
- **Session Management**: Streamlit's built-in secure session handling
- **Database**: SQLite with Alembic migrations (ready for PostgreSQL upgrade)

### Complete User Flow (OAuth + Onboarding)
1. **Login**: User clicks "Sign in with Google" button
2. **OAuth**: Streamlit initiates OAuth flow with Google Identity Services
3. **Authentication**: User authenticates and grants permissions at Google
4. **Callback**: Google redirects back with OAuth data
5. **Sync**: OAuthSyncService syncs OAuth data with user database
6. **Role Check**: System checks if email is in ADMIN_EMAILS and assigns/updates role
7. **Onboarding Check**: System checks if user has completed registration
8. **Registration** (if needed): User fills out registration form with username, emails, consent
9. **Dashboard**: User routed to role-specific dashboard (Admin/Assistant/Student)

### Mock Authentication Flow (Development)
1. User clicks "Mock OAuth" in development mode
2. User enters email and display name in form
3. OAuth2MockService simulates OAuth data structure
4. User record created/updated in database with role assignment
5. Session started with role-based access control

### Environment Configuration

**Step 1: Create `.env` file** (copy from `.env.example`)
```bash
# Required .env variables for Phase 2B
DATABASE_URL="sqlite:///./badging_system.db"  # Use SQLite for development
ADMIN_EMAILS="admin@example.com,admin2@example.com"
LOG_LEVEL="INFO"
DEBUG="true"
```

**Step 2: Create `.streamlit/secrets.toml` file** (required for OAuth)

First, create the `.streamlit` directory if it doesn't exist:
```bash
mkdir -p .streamlit
```

Then create `.streamlit/secrets.toml` with the following content:
```toml
# OAuth Configuration for Google Authentication
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
# Generate cookie_secret with: python -c "import secrets; print(secrets.token_urlsafe(32))"
cookie_secret = "your_32_character_secret_key_here"
client_id = "your_google_client_id.apps.googleusercontent.com"
client_secret = "your_google_client_secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[general]
debug = true
enable_mock_auth = true  # Enable mock OAuth for development
```

**Step 3: Generate cookie secret**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copy the output to `cookie_secret` in `secrets.toml`.

**Important**: Add `.streamlit/secrets.toml` to `.gitignore` - never commit secrets to git!

### Key Files
- `app/services/oauth.py` - OAuth synchronization service for st.user integration
- `app/services/auth.py` - Original authentication service (still used for user management)
- `app/ui/oauth_auth.py` - OAuth authentication UI with st.login() integration
- `app/ui/auth.py` - Legacy authentication UI (Phase 2A, still available)
- `app/models/user.py` - User data model with roles and Google OAuth fields
- `app/core/session.py` - Session management utilities
- `app/core/database.py` - Database connection and health checks
- `tests/unit/test_oauth_service.py` - OAuth service unit tests
- `tests/integration/test_oauth_integration.py` - OAuth integration tests
- `docs/oauth_setup_guide.md` - Complete OAuth setup documentation

### Testing
Run the complete test suite to verify the implementation:
```bash
uv run pytest -v
```

**Test Coverage (Phase 2B):**
- **Total Tests**: 48/48 passing
- **OAuth Unit Tests**: 20 tests (OAuth service logic)
- **OAuth Integration Tests**: 8 tests (end-to-end OAuth flows)
- **Auth Unit Tests**: 5 tests (user management and role assignment)
- **Auth Integration Tests**: 4 tests (database integration)
- **Session Tests**: 6 tests (session management)
- **Core Tests**: 5 tests (smoke tests, config, logging)

**Test Structure:**
- `tests/unit/` - Unit tests with mocked dependencies
- `tests/integration/` - Integration tests with test database (SQLite)
- `tests/test_smoke.py` - Smoke tests for module imports

**Running Specific Tests:**
```bash
# Run only OAuth tests
uv run pytest tests/unit/test_oauth_service.py -v
uv run pytest tests/integration/test_oauth_integration.py -v

# Run with coverage
uv run coverage run -m pytest
uv run coverage report
```

## Testing Strategy

### Current Testing (Phase 2B)
- **Unit tests**: Services with mocked database
- **Integration tests**: End-to-end flows with SQLite test database
- **Coverage target**: 50% minimum (achieved)

### Future Testing (Phases 3-8)
- **Security tests**: Role guard enforcement and PII redaction validation
- **E2E tests**: Playwright-based UI testing
- **Coverage target**: ≥ 80%

## Documentation Structure

### docs/plans/
Contains formal planning documents for each development phase:
- `phase_one_plan.md` through `phase_ten_plan.md`
- Each plan includes objectives, approach, deliverables, acceptance criteria, risks, timeline
- Plans require Alfred Essa approval before execution begins
- Plans must record acceptance before code commits are authorized

### docs/logs/
Contains brief outcome logs for completed phases:
- `phase_[number]_outcome.md` format
- Records completion date, achievements, issues encountered, lessons learned
- Created after phase acceptance

### docs/specs/
Contains technical specifications and requirements:
- `product_requirements.md` - Product requirements document
- `tech_specification.md` - Technical architecture and specifications  
- `project_plan.md` - Overall project plan and timeline
- `ui_ux_specification.md` - UI/UX design specifications

## Important Notes

### Security & Secrets
- **Never commit secrets**: Add `.streamlit/secrets.toml` and `.env` to `.gitignore`
- **OAuth credentials**: Store in `.streamlit/secrets.toml`, not in `.env`
- **Cookie secrets**: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Authentication (Phase 2B)
- **Primary method**: Streamlit native OAuth with `st.login()` and `st.user`
- **Development**: Mock OAuth available when `enable_mock_auth = true` in secrets
- **Admin bootstrap**: Set admin emails in `ADMIN_EMAILS` environment variable
- **User sync**: OAuthSyncService automatically syncs OAuth users with database

### Database
- **Development**: SQLite (`sqlite:///./badging_system.db`)
- **Production**: PostgreSQL (update `DATABASE_URL` in production)
- **Migrations**: Use Alembic for all schema changes
- **Reset dev DB**: `rm badging_system.db && uv run alembic upgrade head`

### Development Workflow
- **Linting**: `uv run ruff check --fix .` before commits
- **Type checking**: `uv run mypy app/` to catch type errors
- **Testing**: `uv run pytest` - all tests must pass
- **Pre-commit**: Hooks automatically run on git commit

### Phase Management
- **CRITICAL**: No code commits without phase acceptance from Alfred Essa
- All phase work must follow the formal planning and approval process
- See `docs/plans/` for phase planning documents

### Future Considerations (Phases 3-8)
- All privileged operations must be audited
- PII redaction is mandatory for all exports
- Server-side role enforcement is critical
- Use structured logging with JSON formatter for production

## Troubleshooting

### OAuth Issues

**Problem**: "OAuth not available" or "st.login() not found"
- **Solution**: Upgrade Streamlit: `uv add "streamlit>=1.42.0" "Authlib>=1.3.2"`

**Problem**: "Invalid redirect URI" error
- **Solution**: Ensure redirect URI in Google Console matches `.streamlit/secrets.toml` exactly
  - Development: `http://localhost:8501/oauth2callback`
  - Production: `https://your-domain.com/oauth2callback`

**Problem**: "Access blocked" during OAuth
- **Solution**: Add test user emails in Google Cloud Console → OAuth consent screen → Test users

**Problem**: OAuth works but user has wrong role
- **Solution**: Check `ADMIN_EMAILS` in `.env` file - must match OAuth email exactly

### Database Issues

**Problem**: "No such table: users" error
- **Solution**: Run migrations: `uv run alembic upgrade head`

**Problem**: Database locked (SQLite)
- **Solution**: Close any open connections or delete `badging_system.db` and re-run migrations

**Problem**: Migrations fail or out of sync
- **Solution**: Reset development database:
  ```bash
  rm badging_system.db
  uv run alembic upgrade head
  ```

### Testing Issues

**Problem**: Tests fail with "No such table" error
- **Solution**: Tests create their own temporary database - check test file imports

**Problem**: Import errors in tests
- **Solution**: Ensure you're running tests with `uv run pytest`, not plain `pytest`

**Problem**: Coverage not generating
- **Solution**: Run `uv run coverage run -m pytest` then `uv run coverage report`

### Configuration Issues

**Problem**: Settings not loading from `.env`
- **Solution**: Ensure `.env` is in project root and `python-dotenv` is installed

**Problem**: Streamlit secrets not found
- **Solution**: Create `.streamlit/secrets.toml` in project root (see Environment Configuration section)

**Problem**: "Cookie secret too short" error
- **Solution**: Generate 32-character secret: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

### Development Issues

**Problem**: Pre-commit hooks failing
- **Solution**: Run fixes manually: `uv run ruff check --fix . && uv run ruff format .`

**Problem**: Type checking errors
- **Solution**: Run `uv run mypy app/` to see detailed errors

**Problem**: Port 8501 already in use
- **Solution**: Find and kill existing Streamlit process or use different port:
  ```bash
  uv run streamlit run app/main.py --server.port 8502
  ```

### Getting Help

- **Phase 2B Documentation**: See `docs/oauth_setup_guide.md`
- **Phase Plans**: Check `docs/plans/` for detailed implementation plans
- **Test Examples**: Look at `tests/unit/` and `tests/integration/` for usage examples