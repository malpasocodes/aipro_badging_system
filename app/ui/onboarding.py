"""Onboarding UI component for collecting user information."""

import streamlit as st

from app.services.onboarding import (
    OnboardingError,
    ValidationError,
    get_onboarding_service,
)


def render_onboarding_form() -> None:
    """
    Render registration/onboarding form for new users.

    Collects username, Substack email, Meetup email, and consent.
    Must be called after authentication when user is not yet onboarded.
    """
    st.markdown("## New User Registration 📝")
    st.markdown(
        "Welcome! Please complete your registration to access the AIPPRO Badging System. "
        "This information helps us verify your participation in the program and personalize your experience."
    )
    st.markdown("---")

    with st.form("onboarding_form", clear_on_submit=False):
        # Username field
        st.markdown("### Your Profile")
        username = st.text_input(
            "Username *",
            max_chars=50,
            placeholder="Enter your display name",
            help="Choose a display name (3-50 characters, letters, numbers, underscores, and hyphens only)",
        )

        # Email fields
        st.markdown("### Program Participation")
        st.info(
            "We need your Substack and Meetup emails to verify your participation "
            "in the AIPPRO program. These emails will be kept private."
        )

        substack_email = st.text_input(
            "Substack Subscription Email *",
            placeholder="your.email@example.com",
            help="Email address you use for your Substack subscription to AIPPRO",
        )

        meetup_email = st.text_input(
            "Meetup Email *",
            placeholder="your.email@example.com",
            help="Email address you use for Meetup.com AIPPRO events",
        )

        # Privacy policy and consent
        st.markdown("---")
        st.markdown("### Privacy & Terms")

        with st.expander("📋 Privacy Policy & Terms of Service"):
            st.markdown("""
**Privacy Policy:**
- Your information will be used solely for badge verification and program administration
- Your email addresses will be kept private and never shared with third parties
- Your username will be visible to instructors and assistants for badge approvals
- You can request data deletion at any time by contacting an administrator

**Terms of Service:**
- You must be an active AIPPRO program participant
- You must provide accurate information for verification purposes
- Badge awards are subject to instructor/assistant approval
- Misrepresentation of participation may result in account suspension
""")

        consent = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy *",
            help="Required to use the badging system",
        )

        st.markdown("---")

        # Form actions
        st.markdown("---")

        submitted = st.form_submit_button(
            "Complete Registration",
            type="primary",
            use_container_width=True,
        )

        # Form submission handling
        if submitted:
            # Validate required fields
            if not username or not username.strip():
                st.error("❌ Username is required")
                return

            if not substack_email or not substack_email.strip():
                st.error("❌ Substack email is required")
                return

            if not meetup_email or not meetup_email.strip():
                st.error("❌ Meetup email is required")
                return

            if not consent:
                st.error("❌ You must agree to the terms to continue")
                return

            # Get current user from OAuth (no session caching)
            from app.ui.oauth_auth import get_current_oauth_user
            current_user = get_current_oauth_user()
            if not current_user:
                st.error("❌ Session error: No authenticated user found")
                return

            # Submit onboarding
            try:
                onboarding_service = get_onboarding_service()
                updated_user = onboarding_service.complete_onboarding(
                    user_id=current_user.id,
                    username=username,
                    substack_email=substack_email,
                    meetup_email=meetup_email,
                )

                # User updated - no session caching needed

                st.success("✅ Registration complete! Welcome to the AIPPRO Badging System.")
                st.info("🔄 Redirecting to your dashboard...")

                # Force page rerun to redirect to main app
                st.rerun()

            except ValidationError as e:
                st.error(f"❌ Validation error: {str(e)}")
            except OnboardingError as e:
                st.error(f"❌ Error completing onboarding: {str(e)}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                # Log the error for debugging
                import logging
                logging.exception("Unexpected error during onboarding")


def render_onboarding_status(user) -> None:
    """
    Render onboarding status for debugging or admin views.

    Args:
        user: User object to check onboarding status
    """
    onboarding_service = get_onboarding_service()
    is_onboarded = onboarding_service.check_onboarding_status(user)

    if is_onboarded:
        st.success(f"✅ User '{user.username}' has completed onboarding")
        st.caption(f"Completed at: {user.onboarding_completed_at}")
    else:
        st.warning("⚠️ User has not completed onboarding")
        missing_fields = []
        if not user.username:
            missing_fields.append("username")
        if not user.substack_email:
            missing_fields.append("Substack email")
        if not user.meetup_email:
            missing_fields.append("Meetup email")
        if not user.onboarding_completed_at:
            missing_fields.append("completion timestamp")

        if missing_fields:
            st.caption(f"Missing: {', '.join(missing_fields)}")
