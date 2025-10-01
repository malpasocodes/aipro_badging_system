"""Domain services - Authentication, onboarding, badges, approvals, exports, and audit."""

from .audit_service import AuditService, get_audit_service
from .auth import AuthService, AuthenticationError, MockAuthService
from .catalog_service import (
    CatalogService,
    get_catalog_service,
    CatalogError,
    AuthorizationError as CatalogAuthorizationError,
    NotFoundError,
    ValidationError as CatalogValidationError,
)
from .oauth import OAuthSyncService, OAuth2MockService, get_oauth_service
from .onboarding import (
    OnboardingService,
    get_onboarding_service,
    OnboardingError,
    ValidationError,
)
from .progress_service import (
    ProgressService,
    get_progress_service,
    ProgressError,
    DuplicateAwardError,
)
from .request_service import (
    RequestService,
    get_request_service,
    RequestError,
    AuthorizationError as RequestAuthorizationError,
)
from .roster_service import (
    RosterService,
    get_roster_service,
    RosterError,
    AuthorizationError as RosterAuthorizationError,
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
