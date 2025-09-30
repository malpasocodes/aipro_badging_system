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

**Current Status:** Phase 2A (Authentication) is complete. The following commands are available:

### Environment Setup
```bash
uv sync --frozen          # Install dependencies from lockfile
```

### Development
```bash
# Run the application locally
uv run streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0

# Linting and formatting
ruff check                # Lint code
ruff format               # Format code

# Type checking
mypy app/                 # Type check application code

# Testing
pytest                    # Run all tests
pytest tests/unit/        # Run unit tests only
pytest tests/integration/ # Run integration tests
coverage run -m pytest    # Run tests with coverage
coverage report           # Show coverage report
```

### Database Operations
```bash
# Database migrations (Alembic configured)
uv run alembic upgrade head      # Apply migrations
uv run alembic revision --autogenerate -m "message"  # Generate new migration
uv run alembic current           # Show current revision
uv run alembic history           # Show migration history
```

## Architecture Highlights

### Data Model
- **users**: Google OAuth integration with roles (admin/assistant/student)
- **Badge Hierarchy**: programs → skills → mini_badges → capstones
- **requests**: Badge approval workflow with audit trail
- **awards**: Earned badges with automatic progression logic
- **notifications**: In-app messaging system
- **audit_logs**: Complete audit trail for all privileged operations

### Key Services
- **AuthService**: Google OAuth integration and role management
- **CatalogService**: CRUD operations for badge hierarchy
- **RequestService**: Badge request submission and approval workflow
- **ProgressService**: Automatic award calculation and progression logic
- **ExportService**: PII-compliant data exports for administrators
- **NotificationService**: In-app notifications

### Security & Privacy
- Google Identity Services OAuth with PKCE
- Role-based access control (RBAC) with server-side enforcement
- Comprehensive PII redaction for all exports
- Complete audit logging for privileged operations
- Signed session cookies with CSRF protection

### Business Rules
- Badge progression: Program → Skills → Mini-badges (strict DAG)
- Skill awards granted when ALL child mini-badges are approved
- Program awards granted when ALL skills are awarded (+ optional capstone)
- Requests are immutable after decision (new request required for changes)
- No badge expiration in v1

## Deployment Configuration

**Platform:** Render
- **Web Service:** Streamlit app
- **Database:** Managed PostgreSQL
- **Environment Variables:**
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - `DATABASE_URL`
  - `APP_SECRET_KEY`
  - `APP_ENV` (prod/staging/dev)
  - `LOG_LEVEL`

**Build Commands:**
- Build: `uv sync --frozen`
- Start: `uv run streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`

## Development Guidelines

### Role-Based Features
- **Students**: Request mini-badges, view progress, receive notifications
- **Assistants**: Approve/reject requests, manage roster (cannot delete accounts or retire badges)
- **Administrators**: Full control including catalog management, exports, and all assistant capabilities

### UI/UX Patterns
- Streamlit sidebar for global navigation
- Role-aware content and actions
- PII masking in all user interfaces (e.g., `al***@domain.com`)
- Toast notifications for user feedback
- Comprehensive form validation with inline errors

### Performance Considerations
- Page render targets: p95 < 800ms (cached), < 1500ms (cold)
- Pagination for all data tables (25 rows default)
- Query optimization with proper indexing
- `st.cache_data` for read-only catalog data (5m TTL)

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
2. ✅ **Authentication & Session Management** - Phase 2A Complete (Mock Authentication)
   - Phase 2B: Real Google OAuth (Planned)
   - Phase 2C: Enhanced Security (Planned)

### Upcoming Phases  
3. Onboarding Flow
4. Roles & Approvals Queue
5. Badge Data Model & Catalog
6. Earning Logic & Awards
7. Notifications & Audit Trails
8. Exports & PII Redaction
9. UX Polish & Accessibility
10. Deployment & Launch

**Note:** No phase can begin without an approved plan document in `docs/plans/`.

## Current Authentication System (Phase 2A)

### Implementation Status
- **Mock Authentication**: Fully functional development authentication system
- **User Management**: Complete user CRUD with SQLite database
- **Session Management**: Streamlit session_state with timeout handling
- **Role-Based Access**: Admin/student roles with environment-based bootstrap
- **Database**: SQLite with Alembic migrations (ready for PostgreSQL upgrade)

### Authentication Flow
1. User enters email in mock sign-in form
2. MockAuthService simulates Google ID token verification  
3. User record created/updated in database
4. Session started with role-based access control
5. UI adapts based on user role (admin vs student)

### Environment Configuration
```bash
# Required .env variables for Phase 2A
DATABASE_URL="sqlite:///./badging_system.db"
GOOGLE_CLIENT_ID="your_google_client_id_here"  # For Phase 2B
ADMIN_EMAILS="admin@example.com,admin2@example.com"
LOG_LEVEL="INFO"
DEBUG="true"
```

### Key Files
- `app/services/auth.py` - Authentication service with mock implementation
- `app/models/user.py` - User data model with roles and Google OAuth fields
- `app/ui/auth.py` - Streamlit authentication UI components
- `app/core/session.py` - Session management with timeout
- `app/core/database.py` - Database connection and health checks
- `tests/unit/test_auth_service.py` - Comprehensive authentication tests
- `tests/integration/test_auth_integration.py` - End-to-end auth flow tests

### Testing
- **Unit Tests**: 11/11 passing (authentication service)
- **Integration Tests**: 4/4 passing (database and user flows)
- **Mock Coverage**: Complete test coverage without external API dependencies

## Testing Strategy
- **Unit tests**: Services with mocked DAL
- **Integration tests**: DAL against test PostgreSQL
- **Security tests**: Role guard enforcement and PII redaction validation
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
- Never commit secrets or API keys
- All privileged operations must be audited
- PII redaction is mandatory for all exports
- Server-side role enforcement is critical
- Use structured logging with JSON formatter for production
- **CRITICAL**: No code commits without phase acceptance from Alfred Essa
- All phase work must follow the formal planning and approval process