# Django Query Budget documentation build configuration

project = "Django Query Budget"
copyright = "2026, Django Query Budget Contributors"
author = "Django Query Budget Contributors"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
]

# MyST settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

# Autodoc
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", "https://docs.djangoproject.com/en/stable/_objects/"),
}

# Theme
html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/your-org/django-query-budget",
    "source_branch": "main",
    "source_directory": "docs/",
}

# Source
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build", "superpowers"]
