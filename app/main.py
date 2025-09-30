"""Main entry point for the AIPPRO Badging System Streamlit application."""

import streamlit as st

from app.core.config import get_settings
from app.core.logging import setup_logging


def main() -> None:
    """Main application entry point."""
    # Initialize logging
    setup_logging()

    # Load configuration (will be used in future phases)
    _ = get_settings()

    # Set page configuration
    st.set_page_config(
        page_title="AIPPRO Badging System",
        page_icon="🏆",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Simple placeholder for Phase 1
    st.title("🏆 AIPPRO Badging System")
    st.write("Welcome to the AIPPRO Digital Badging System")

    st.info(
        "This is Phase 1 - Project scaffolding complete! "
        "Authentication and core features will be added in subsequent phases."
    )

    # Health check endpoint (accessible via query params)
    if st.query_params.get("health"):
        st.json({"status": "healthy", "version": "0.1.0", "phase": "1"})


if __name__ == "__main__":
    main()
