"""Dependency Management for BlenderPhotonics

* Authors: (c) 2021-2022 Qianqian Fang <q.fang at neu.edu>
* License: GNU General Public License V3 or later (GPLv3)
* Website: http://mcx.space/bp

This module handles the import and installation of external dependencies
for BlenderPhotonics, providing graceful fallbacks when packages are missing.
"""

import sys
import importlib
import bpy

# Global flags to track which dependencies are available
DEPENDENCIES = {
    "jdata": False,
    "numpy": False,
    "iso2mesh": False,
    "pmcx": False,
    "pmmc": False,
}

# Error messages for missing dependencies
MISSING_MESSAGES = {
    "jdata": "JData package is required for JSON/JMesh file operations",
    "numpy": "NumPy package is required for numerical operations",
    "iso2mesh": "iso2mesh package is required for mesh generation operations",
    "pmcx": "pmcx package is required for Monte Carlo eXtreme simulations",
    "pmmc": "pmmc package is required for Mesh-based Monte Carlo simulations",
}


def try_import(module_name):
    """Try to import a module and return True if successful, False otherwise."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def check_dependencies():
    """Check which dependencies are available and update the global flags."""
    for dep in DEPENDENCIES:
        DEPENDENCIES[dep] = try_import(dep)
    return DEPENDENCIES


def get_missing_dependencies():
    """Return a list of missing dependencies."""
    check_dependencies()
    return [dep for dep, available in DEPENDENCIES.items() if not available]


def require_dependency(module_name, operation_name="this operation"):
    """Check if a dependency is available, show error if not."""
    if not DEPENDENCIES.get(module_name, False):
        message = f"{MISSING_MESSAGES.get(module_name, f'{module_name} is required')} for {operation_name}. Please install it using the buttons in the BlenderPhotonics panel."
        show_error_message(message)
        return False
    return True


def show_error_message(message, title="Missing Dependency"):
    """Show an error message to the user."""

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon="ERROR")


def safe_import(module_name, fallback=None):
    """Safely import a module, returning fallback if import fails."""
    try:
        # Suppress specific warnings for pmmc binary extension issues
        if module_name == "pmmc":
            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=".*pmmc binary extension.*")
                return importlib.import_module(module_name)
        else:
            return importlib.import_module(module_name)
    except ImportError:
        if fallback is not None:
            return fallback
        return None


# Initialize dependency check
check_dependencies()
