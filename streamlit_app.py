"""Streamlit app entry point for deployment.

This file exists at the project root to ensure proper Python path resolution
when running on deployment platforms like Render.
"""

# Import and run the main app
from app.main import main

if __name__ == "__main__":
    main()
