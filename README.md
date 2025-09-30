# AIPPRO Badging System

A Python/Streamlit application for recognizing and tracking student achievement through digital badges. The system supports identity verification, onboarding, role-based approvals, and progression from mini-badges to capstones.

[![CI](https://github.com/alfredessa/aippro-badging-system/workflows/CI/badge.svg)](https://github.com/alfredessa/aippro-badging-system/actions)
[![Coverage](https://codecov.io/gh/alfredessa/aippro-badging-system/branch/main/graph/badge.svg)](https://codecov.io/gh/alfredessa/aippro-badging-system)

## 🚀 Tech Stack

- **Python 3.11+** - Modern Python with type hints
- **Streamlit** - Web application framework
- **uv** - Fast package management and virtual environments
- **PostgreSQL** - Database (Phase 4-5)
- **Google Identity Services** - OAuth authentication (Phase 2)
- **Render** - Cloud deployment platform

## 📁 Project Structure

```
/app
  /core          # Configuration, logging, security utilities
  /ui            # UI helpers, components, Streamlit theming
  /models        # Pydantic models and ORM schema definitions
  /services      # Domain services (auth, badges, approvals, etc.)
  /dal           # Data access layer and repository patterns
  /routers       # Streamlit page controllers and routing
/docs
  /plans         # Phase planning documents
  /logs          # Phase execution outcome logs
  /specs         # Technical specifications and requirements
/tests
  /unit          # Unit tests with mocked dependencies
  /integration   # Integration tests with test database
  /e2e           # End-to-end tests (future Playwright setup)
```

## 🛠️ Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/alfredessa/aippro-badging-system.git
   cd aippro-badging-system
   ```

2. **Install dependencies**
   ```bash
   uv sync --extra dev
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

5. **Run the application**
   ```bash
   uv run streamlit run app/main.py
   ```

   The application will be available at `http://localhost:8501`

## 🧪 Development Commands

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run coverage run -m pytest
uv run coverage report

# Run specific test types
uv run pytest tests/unit/          # Unit tests only
uv run pytest tests/integration/   # Integration tests only
```

### Code Quality
```bash
# Linting and formatting
uv run ruff check .                # Check for issues
uv run ruff check --fix .          # Fix auto-fixable issues
uv run ruff format .               # Format code

# Type checking
uv run mypy app/

# Security scanning
uv run safety check               # Check for known vulnerabilities
```

### Development Workflow
```bash
# Format and check code (runs automatically with pre-commit)
uv run ruff format . && uv run ruff check . && uv run mypy app/

# Run tests before committing
uv run pytest --cov=app --cov-report=term-missing
```

## 🏗️ Phase-Based Development

This project follows a structured 10-phase development approach:

### Phase 1: Project Setup & Repo Initialization ✅
- [x] Python environment with uv package management
- [x] Complete project structure
- [x] CI/CD pipeline with GitHub Actions
- [x] Development tooling configuration
- [x] Baseline documentation

### Phase 2: Authentication & Session Management (Next)
- Google Sign-In with email verification
- Session management and user roles
- Basic user table integration

### Upcoming Phases
- Phase 3: Onboarding Flow
- Phase 4: Roles & Approvals Queue
- Phase 5: Badge Data Model & Catalog
- Phase 6: Earning Logic & Awards
- Phase 7: Notifications & Audit Trails
- Phase 8: Exports & PII Redaction
- Phase 9: UX Polish & Accessibility
- Phase 10: Deployment & Launch

Each phase requires formal planning, approval, and acceptance before proceeding. See `docs/plans/` for detailed phase documentation.

## 🔒 Security & Privacy

- **PII Redaction**: All exports automatically strip personally identifiable information
- **Role-Based Access Control**: Server-side enforcement of user permissions
- **Audit Logging**: Complete audit trail for all privileged operations
- **Secure Configuration**: Environment-based secrets management

## 🧪 Testing Strategy

- **Unit Tests**: Services with mocked dependencies
- **Integration Tests**: Data access layer against test database
- **Security Tests**: Role enforcement and PII redaction validation
- **Coverage Target**: 50% minimum (Phase 1), scaling to 80% by Phase 3-4

## 📋 Available Commands

### Core Development
- `uv sync` - Install/update dependencies
- `uv run streamlit run app/main.py` - Start development server
- `uv run pytest` - Run test suite
- `uv run ruff format .` - Format code
- `uv run mypy app/` - Type checking

### Quality Assurance
- `uv run coverage run -m pytest` - Test with coverage
- `uv run safety check` - Security vulnerability scan
- `uv run pre-commit run --all-files` - Run all quality checks

## 🚀 Deployment

The application is designed for deployment on [Render](https://render.com/) with:

- **Build Command**: `uv sync --frozen`
- **Start Command**: `uv run streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`
- **Health Check**: Available at `/?health`

## 📝 Contributing

1. **Follow the Phase Process**: All development must follow the formal phase planning and approval process documented in `CLAUDE.md`

2. **Code Quality**: All code must pass linting, type checking, and tests
   ```bash
   uv run pre-commit run --all-files
   uv run pytest --cov=app
   ```

3. **Testing**: Maintain test coverage and add tests for new functionality

4. **Documentation**: Update documentation for any new features or changes

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Guidance for Claude Code development
- **[docs/specs/](docs/specs/)** - Technical specifications and requirements
- **[docs/plans/](docs/plans/)** - Phase planning documents
- **[docs/logs/](docs/logs/)** - Phase execution outcome logs

## 🔗 Health Check

The application includes a basic health check endpoint accessible at `/?health` that returns:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "phase": "1"
}
```

## 🧑‍💻 Development Notes

- **Database dependencies** are configured but deferred until Phase 4-5
- **Pre-commit hooks** automatically format code and run quality checks
- **VS Code integration** includes recommended extensions and settings
- **Environment variables** are managed through `.env` file (see `.env.example`)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- **Alfred Essa** - Project Lead and Developer

---

**Current Status**: Phase 1 Complete - Project scaffolding and development environment established.