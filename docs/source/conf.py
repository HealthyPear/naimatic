# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib

import naimatic


pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
pyproject = tomllib.loads(pyproject_path.read_text())

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = pyproject["project"]["name"]
author = pyproject["project"]["authors"][0]["name"]
copyright = "{}.  Last updated {}".format(
    author, datetime.datetime.now().strftime("%d %b %Y %H:%M")
)

version = naimatic.__version__
# The full version, including alpha/beta/rc tags.
release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_changelog",
    "autoapi.extension",
    "sphinx_copybutton",
    "sphinx.ext.autosummary",
    "sphinxcontrib.autodoc_pydantic",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]

# -- Options for sphinx-autoapi output -------------------------------------------------
# https://sphinx-autoapi.readthedocs.io/en/latest/index.html
autoapi_dirs = ["../../src"]
autodoc_typehints = "description"
autoapi_ignore = ["*version*", "*config.py*"]

# -- Options for autodoc-pydantic output -------------------------------------------------
# https://autodoc-pydantic.readthedocs.io/en/stable/
autosummary_generate = True
autodoc_pydantic_model_show_json = True
autodoc_pydantic_settings_show_json = False
autodoc_pydantic_model_show_json_error_strategy = "coerce"
