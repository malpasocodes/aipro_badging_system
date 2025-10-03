"""Domain services - Authentication, onboarding, badges, approvals, exports, and audit."""

from .audit_service import AuditService, get_audit_service
from .auth import AuthenticationError, AuthService, MockAuthService
from .catalog_service import (
    AuthorizationError as CatalogAuthorizationError,
)
from .catalog_service import (
    CatalogError,
    CatalogService,
    NotFoundError,
    get_catalog_service,
)
from .catalog_service import (
    ValidationError as CatalogValidationError,
)
from .oauth import OAuth2MockService, OAuthSyncService, get_oauth_service
from .onboarding import (
    OnboardingError,
    OnboardingService,
    ValidationError,
    get_onboarding_service,
)
from .progress_service import (
    DuplicateAwardError,
    ProgressError,
    ProgressService,
    get_progress_service,
)
from .request_service import (
    AuthorizationError as RequestAuthorizationError,
)
from .request_service import (
    RequestError,
    RequestService,
    get_request_service,
)
from .roster_service import (
    AuthorizationError as RosterAuthorizationError,
)
from .roster_service import (
    RosterError,
    RosterService,
    get_roster_service,
)

__all__ = [
    "AuditService",
    "get_audit_service",
    "AuthService",
    "AuthenticationError",
    "MockAuthService",
    "CatalogService",
    "get_catalog_service",
    "CatalogError",
    "CatalogAuthorizationError",
    "NotFoundError",
    "CatalogValidationError",
    "OAuthSyncService",
    "OAuth2MockService",
    "get_oauth_service",
    "OnboardingService",
    "get_onboarding_service",
    "OnboardingError",
    "ValidationError",
    "ProgressService",
    "get_progress_service",
    "ProgressError",
    "DuplicateAwardError",
    "RequestService",
    "get_request_service",
    "RequestError",
    "RequestAuthorizationError",
    "RosterService",
    "get_roster_service",
    "RosterError",
    "RosterAuthorizationError",
]
