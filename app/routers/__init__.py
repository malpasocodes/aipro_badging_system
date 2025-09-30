"""Streamlit page controllers and routing."""

from .admin import render_admin_dashboard
from .assistant import render_assistant_dashboard
from .student import render_student_dashboard

__all__ = [
    "render_admin_dashboard",
    "render_assistant_dashboard",
    "render_student_dashboard",
]
