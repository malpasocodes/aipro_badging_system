"""Domain services - Authentication, onboarding, badges, approvals, exports, and audit."""

from .audit_service import AuditService, get_audit_service
from .auth import AuthService, AuthenticationError, MockAuthService
from .oauth import OAuthSyncService, OAuth2MockService, get_oauth_service
from .onboarding import (
    OnboardingService,
    get_onboarding_service,
    OnboardingError,
    ValidationError,
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
    "OAuthSyncService",
    "OAuth2MockService",
    "get_oauth_service",
    "OnboardingService",
    "get_onboarding_service",
    "OnboardingError",
    "ValidationError",
    "RequestService",
    "get_request_service",
    "RequestError",
    "RequestAuthorizationError",
    "RosterService",
    "get_roster_service",
    "RosterError",
    "RosterAuthorizationError",
]
