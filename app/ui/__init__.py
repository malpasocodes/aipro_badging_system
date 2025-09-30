"""UI helpers, components, and Streamlit theming."""

from .auth import (
    render_google_signin,
    render_user_info,
    get_current_user,
    require_authentication,
    require_admin
)
from .oauth_auth import (
    render_oauth_signin,
    render_oauth_user_info,
    get_current_oauth_user,
    require_oauth_authentication,
    require_oauth_admin,
    is_oauth_available
)
from .onboarding import (
    render_onboarding_form,
    render_onboarding_status
)

__all__ = [
    # Legacy authentication (Phase 2A)
    "render_google_signin",
    "render_user_info",
    "get_current_user",
    "require_authentication",
    "require_admin",
    # OAuth authentication (Phase 2B)
    "render_oauth_signin",
    "render_oauth_user_info",
    "get_current_oauth_user",
    "require_oauth_authentication",
    "require_oauth_admin",
    "is_oauth_available",
    # Onboarding (Phase 3)
    "render_onboarding_form",
    "render_onboarding_status"
]
