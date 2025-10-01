"""UI helpers, components, and Streamlit theming."""

from .approval_queue import render_approval_queue
from .auth import (
    render_google_signin,
    render_user_info,
    get_current_user,
    require_authentication,
    require_admin
)
from .award_management import render_award_management
from .badge_display import (
    render_badge_card,
    render_mini_badge_list,
    render_skill_card,
    render_program_card,
    render_award_badge,
    render_progress_summary,
)
from .badge_picker import render_badge_picker, render_badge_picker_compact
from .catalog_browser import render_catalog_browser, render_catalog_search
from .catalog_management import render_catalog_management
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
from .progress_dashboard import (
    render_my_badges,
    render_my_progress,
    render_skill_detail,
    render_program_detail,
    render_progress_dashboard,
)
from .request_form import render_request_form, render_user_requests
from .roster import render_roster

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
    "render_onboarding_status",
    # Requests and Approvals (Phase 4)
    "render_request_form",
    "render_user_requests",
    "render_approval_queue",
    "render_roster",
    "render_award_management",
    # Catalog Management (Phase 5)
    "render_badge_picker",
    "render_badge_picker_compact",
    "render_catalog_browser",
    "render_catalog_search",
    "render_catalog_management",
    # Progress & Awards (Phase 6)
    "render_badge_card",
    "render_mini_badge_list",
    "render_skill_card",
    "render_program_card",
    "render_award_badge",
    "render_progress_summary",
    "render_my_badges",
    "render_my_progress",
    "render_skill_detail",
    "render_program_detail",
    "render_progress_dashboard",
]
