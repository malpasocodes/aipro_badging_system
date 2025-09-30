# Phase One Plan: Project Setup & Repo Initialization

**Project:** AIPPRO Badging System  
**Phase:** 1 of 10  
**Created:** 2025-09-30  
**Status:** Pending Approval

---

## Objectives

Establish the foundational project scaffolding and development workflow for the AIPPRO Badging System. This phase will create a robust, reproducible development environment with automated quality checks and testing infrastructure.

**Primary Goals:**
- Set up Python 3.11+ environment with uv package management
- Create complete project structure following technical specifications
- Implement CI/CD pipeline with GitHub Actions
- Configure development tooling for code quality and testing
- Establish baseline for all subsequent development phases

---

## Detailed Approach

### 1. Environment and Package Management
- **Python Version**: 3.11+ (required for modern typing features)
- **Package Manager**: uv for fast, reliable dependency resolution and virtual environment management
- **Lockfile Strategy**: Use `uv.lock` for reproducible builds across environments

### 2. Project Structure Implementation
Create the complete directory structure as specified in technical documentation:

```
/app
  /core          # Configuration, logging, security utilities
  /ui            # UI helpers, components, Streamlit theming
  /models        # Pydantic models and ORM schema definitions
  /services      # Domain services (auth, badges, approvals, etc.)
  /dal           # Data access layer and repository patterns
  /routers       # Streamlit page controllers and routing
/tests
  /unit          # Unit tests with mocked dependencies
  /integration   # Integration tests with test database
  /e2e           # End-to-end tests (future Playwright setup)
/docs            # Existing documentation structure maintained
```

### 3. Dependency Configuration
**Core Dependencies (Phase 1):**
- `streamlit` - Web application framework
- `pydantic` - Data validation and settings management
- `structlog` - Structured logging
- `python-dotenv` - Environment variable management

**Future Dependencies (Phase 4-5):**
- `sqlmodel` - Database ORM with type safety (deferred until database integration)
- `psycopg[binary]` - PostgreSQL adapter (deferred until database integration)
- `alembic` - Database migrations (deferred until database integration)

**Development Dependencies:**
- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support (for future async code)
- `coverage` - Code coverage measurement
- `ruff` - Fast Python linter and formatter
- `mypy` - Static type checking
- `pre-commit` - Git hooks for code quality
- `safety` - Dependency vulnerability scanning

**Note**: Database dependencies are included in pyproject.toml but marked as optional for Phase 1 to avoid requiring a running database during initial development and CI setup.

### 4. CI/CD Pipeline Configuration
**GitHub Actions Workflow:**
- **Triggers**: Push to main, pull requests
- **Python Setup**: Use actions/setup-python with Python 3.11
- **Dependency Installation**: `uv sync --frozen` for consistent environment
- **Quality Checks**:
  - Linting with `ruff check`
  - Code formatting check with `ruff format --check`
  - Type checking with `mypy`
  - Tests with `pytest` and coverage reporting
  - Dependency vulnerability scanning with `safety`
- **Coverage Requirement**: Minimum 50% test coverage for Phase 1 (with minimal smoke tests), scaling to 80% by Phase 3-4 when substantial functionality exists
- **Artifacts**: Coverage reports and test results

### 5. Development Tooling
- **Pre-commit Hooks**: 
  - `ruff format` (autofix formatting issues)
  - `ruff check` (linting validation)
  - `mypy` (type checking)
  - `trailing-whitespace` and `end-of-file-fixer` (file cleanup)
  - `check-merge-conflict` (prevent accidental commits)
- **VS Code Integration**:
  - `.vscode/extensions.json` with recommended extensions (Python, Ruff, Mypy)
  - `.vscode/settings.json` with project-specific configurations
  - `.editorconfig` for consistent formatting across IDEs
- **Git Configuration**: Comprehensive .gitignore for Python projects
- **Environment Setup**: `.env.example` template for environment variables

---

## Deliverables

### 1. Configuration Files
- [ ] `pyproject.toml` - Complete project configuration with phased dependencies
- [ ] `uv.lock` - Locked dependency versions for reproducibility
- [ ] `.gitignore` - Python-specific ignore patterns
- [ ] `.pre-commit-config.yaml` - Pre-commit hook configuration with autofix
- [ ] `.editorconfig` - Cross-IDE formatting consistency
- [ ] `.env.example` - Environment variable template
- [ ] `README.md` - Project setup and development instructions

### 2. CI/CD Infrastructure
- [ ] `.github/workflows/ci.yml` - GitHub Actions workflow with vulnerability scanning
- [ ] CI pipeline validates: linting, type checking, tests, coverage, security

### 3. Project Structure
- [ ] Complete `/app` directory structure with placeholder `__init__.py` files
- [ ] `/tests` directory with initial test structure and minimal smoke tests
- [ ] Placeholder modules in each subdirectory for immediate CI validation
- [ ] Basic health check endpoint stub for future deployment

### 4. VS Code Integration
- [ ] `.vscode/extensions.json` - Recommended development extensions
- [ ] `.vscode/settings.json` - Project-specific IDE configurations

### 5. Development Environment
- [ ] Virtual environment created with uv
- [ ] Core dependencies installed and verified (database deps deferred)
- [ ] Development tools functional (ruff, mypy, pytest)
- [ ] Basic logging configuration implemented

### 7. Documentation Structure
- [ ] Updated README.md with:
  - Project overview and tech stack
  - Development setup instructions
  - Available commands and workflows
  - Contribution guidelines
  - Phase-based development process
- [ ] Prepared `docs/logs/` directory for phase outcome tracking
- [ ] Documentation structure aligned with CLAUDE.md specifications

---

## Acceptance Criteria

### Technical Validation
1. **CI Pipeline Success**: GitHub Actions workflow passes completely on skeleton with minimal smoke tests
2. **Environment Reproducibility**: `uv sync --frozen` installs core dependencies without requiring database
3. **Code Quality Tools**: All linting and type checking tools run without errors on placeholder code
4. **Test Infrastructure**: pytest executes successfully with minimal smoke tests achieving 50% coverage baseline
5. **Project Structure**: Directory structure exactly matches technical specification
6. **Security**: Dependency vulnerability scanning passes without critical issues

### Functional Validation
1. **Development Workflow**: Developer can clone repo, run setup commands, and begin development
2. **Quality Gates**: Pre-commit hooks prevent commits that would fail CI
3. **Documentation**: README provides clear, actionable setup instructions
4. **Consistency**: All configuration aligns with technical specifications

### Performance Criteria
1. **CI Speed**: Full CI pipeline completes in under 5 minutes (without database overhead)
2. **Setup Time**: New developer can set up environment in under 10 minutes
3. **Tool Performance**: Linting and type checking complete in under 30 seconds
4. **Health Check**: Basic health endpoint responds within 100ms for future monitoring

---

## Risks and Mitigation Strategies

### Risk 1: Misconfigured CI Pipeline
- **Impact**: High - Blocks all future development
- **Probability**: Medium
- **Mitigation**: Use proven GitHub Actions templates, test with minimal commits
- **Contingency**: Have backup workflow configurations ready

### Risk 2: Dependency Conflicts
- **Impact**: Medium - Could delay development start
- **Probability**: Low (uv has robust resolution, database deps deferred)
- **Mitigation**: Use conservative, well-tested dependency versions; defer database dependencies to reduce complexity
- **Contingency**: Alternative package versions identified in advance

### Risk 3: Incomplete Project Structure
- **Impact**: Medium - Could cause confusion in later phases
- **Probability**: Low
- **Mitigation**: Follow technical specification exactly, use checklists
- **Contingency**: Structure can be refined in early phases if needed

### Risk 4: Tool Version Incompatibilities
- **Impact**: Medium - Could affect development experience
- **Probability**: Low
- **Mitigation**: Pin specific versions of development tools
- **Contingency**: Document known working versions, provide alternatives

---

## Dependencies

### Prerequisites
- Git repository access and appropriate permissions
- Python 3.11+ available in development environment
- uv package manager installed

### External Dependencies
- GitHub repository for CI/CD
- No external services required for this phase

### Internal Dependencies
- Approval of this plan document
- Access to existing documentation in `docs/specs/`

---

## Timeline

**Estimated Duration:** 1-2 days

**Milestones:**
1. **Day 1 Morning**: Project structure and pyproject.toml configuration
2. **Day 1 Afternoon**: CI/CD pipeline setup and initial testing
3. **Day 2 Morning**: Development tooling configuration and validation
4. **Day 2 Afternoon**: Documentation completion and final testing

**Critical Path:**
1. pyproject.toml configuration → dependency installation
2. Project structure creation → CI pipeline setup
3. CI pipeline validation → documentation completion

---

## Success Metrics

1. **Technical Metrics**:
   - CI pipeline passes with 100% success rate (without database dependencies)
   - All development tools (ruff, mypy, pytest, safety) execute without errors
   - Project structure matches specification exactly
   - Basic health check endpoint implemented and functional

2. **Process Metrics**:
   - Setup instructions tested with realistic developer workflow
   - Pre-commit hooks provide helpful autofix experience
   - VS Code integration enhances developer experience
   - Phase deliverables meet acceptance criteria

3. **Quality Metrics**:
   - Code quality tools configured with appropriate rules
   - Test infrastructure ready for immediate use in Phase 2
   - Development workflow is efficient and user-friendly
   - Environment template and logging configuration ready for extension

---

## Next Steps After Completion

Upon successful completion and acceptance of this phase:
1. Plan document will be updated with acceptance timestamp
2. Outcome log will be created in `docs/logs/phase_one_outcome.md`
3. Code will be committed with reference to phase acceptance
4. Phase Two planning can commence

---

## APPROVAL

**Status:** Approved  
**Reviewed by:** Alfred Essa  
**Date:** 2025-09-30 16:30 UTC  
**Notes:** Approved to proceed with Phase One implementation. Plan addresses feedback on database dependencies, coverage requirements, and development tooling.

---

## ACCEPTANCE

**Status:** Accepted  
**Accepted by:** Alfred Essa  
**Date:** 2025-09-30 17:45 UTC  
**Final Completion:** 2025-09-30 22:15 UTC (after addressing uv initialization)  
**Outcome:** Phase One successfully completed with critical uv initialization fix. All deliverables implemented including project structure, CI/CD pipeline, development tooling, and comprehensive documentation. Missing uv.lock generation was identified and resolved.  
**Notes:** Project scaffolding complete with functional development environment. Critical gap in uv initialization was discovered and fixed, ensuring reproducible builds and proper dependency management. Code can now be committed to repository.