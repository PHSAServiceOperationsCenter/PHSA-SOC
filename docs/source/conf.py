# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import socket
import sys

import django
from django.conf import settings


sys.path.insert(0, os.path.abspath('../../'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'p_soc_auto.settings'
django.setup()


# -- Project information -----------------------------------------------------

project = 'SOC Automation and Orchestration'
copyright = (
    '2018 - 2019 Provincial Health Service Authority of British Columbia')
author = 'serban teodorescu, serban.teodoresch@phsa.ca'

# The full version, including alpha/beta/rc tags
release = '0.7.4-dev'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'IPython.sphinxext.ipython_directive',
    'IPython.sphinxext.ipython_console_highlighting',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.inheritance_diagram',
    'celery.contrib.sphinx',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.todo',
    'sphinx.ext.autosummary',
]

todo_include_todos = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#=========================================================================
# html_theme = 'classic'
# html_theme_options = {
#     'rightsidebar': False,
#     'stickysidebar': True,
#     'collapsiblesidebar': False,
#     'externalrefs': True,
# }
#=========================================================================
#html_theme = 'nature'
html_theme = 'sphinxdoc'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3.6', None),
    'django': ('http://docs.djangoproject.com/en/2.2/',
               'http://docs.djangoproject.com/en/2.2/_objects/'), }

autodoc_default_options = {
    'member-order': 'bysource',
    'undoc-members': True,
    'exclude-members': '__weakref__',
}
