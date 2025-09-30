"""Smoke tests to verify basic functionality."""

import importlib


class TestSmokeTests:
    """Basic smoke tests for application structure."""

    def test_app_module_imports(self) -> None:
        """Test that main app modules can be imported."""
        import app
        import app.core
        import app.dal
        import app.models
        import app.routers
        import app.services
        import app.ui

        assert app.__version__ == "0.1.0"

    def test_core_modules_import(self) -> None:
        """Test that core modules can be imported."""
        from app.core import config, logging

        assert hasattr(config, "get_settings")
        assert hasattr(logging, "setup_logging")
        assert hasattr(logging, "get_logger")

    def test_main_module_imports(self) -> None:
        """Test that main module imports successfully."""
        from app import main

        assert hasattr(main, "main")
        assert callable(main.main)

    def test_test_structure_exists(self) -> None:
        """Test that test structure is properly set up."""
        import tests
        import tests.e2e
        import tests.integration
        import tests.unit

        # Basic existence check
        assert tests is not None

    def test_package_structure_complete(self) -> None:
        """Test that all expected packages exist."""
        expected_modules = [
            "app",
            "app.core",
            "app.ui",
            "app.models",
            "app.services",
            "app.dal",
            "app.routers",
        ]

        for module_name in expected_modules:
            module = importlib.import_module(module_name)
            assert module is not None
