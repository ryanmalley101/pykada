"""Sphinx configuration for pykada documentation."""

import os
import sys

# Make the pykada package importable without installing it
sys.path.insert(0, os.path.abspath(".."))

# ---------------------------------------------------------------------------
# Project metadata
# ---------------------------------------------------------------------------
project = "pykada"
copyright = "2026, Ryan Malley"
author = "Ryan Malley"
release = "1.0.2"

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",              # Core: pull docstrings from source
    "sphinx.ext.napoleon",             # Support for Google/NumPy style (plus RST)
    "sphinx.ext.viewcode",             # Add [source] links beside each symbol
    "sphinx.ext.intersphinx",          # Cross-link to Python stdlib & requests docs
    "sphinx_autodoc_typehints",        # Render type annotations in param/return lines
]

# ---------------------------------------------------------------------------
# autodoc settings
# ---------------------------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": False,      # Skip members with no docstring
    "show-inheritance": True,
    "member-order": "bysource",  # Keep definition order, not alphabetical
}
autodoc_typehints = "description"   # Emit type info in param/return, not signature
autodoc_typehints_format = "short"  # e.g. "dict" not "builtins.dict"
autoclass_content = "both"          # Include both class and __init__ docstrings

# ---------------------------------------------------------------------------
# napoleon settings (we use RST-style, but napoleon handles Google too)
# ---------------------------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_rtype = True
napoleon_use_param = True

# ---------------------------------------------------------------------------
# intersphinx
# ---------------------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.readthedocs.io/en/latest/", None),
}

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------
html_theme = "furo"
html_title = "pykada"
html_static_path = ["_static"]

# Optional: set a custom logo in _static/ and reference it here
# html_logo = "_static/logo.svg"
# html_favicon = "_static/favicon.ico"

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}

# ---------------------------------------------------------------------------
# General
# ---------------------------------------------------------------------------
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
