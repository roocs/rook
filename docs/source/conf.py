#!/usr/bin/env python
#
# rook documentation build configuration file, created by
# sphinx-quickstart on Fri Jun  9 13:47:02 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory is
# relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#
import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("../../"))

# -- General configuration ---------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.imgconverter",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "IPython.sphinxext.ipython_console_highlighting",
    "nbsphinx",
    "pywps.ext_autodoc",
]

# To avoid having to install these and burst memory limit on ReadTheDocs.
# List of all tested working mock imports from all birds so new birds can
# inherit without having to test which work which do not.
autodoc_mock_imports = [
    "affine",
    "bottleneck",
    "cairo",
    "cartopy",
    "cftime",
    "dask",
    "fiona",
    "gdal",
    "geopandas",
    "geos",
    "geotiff",
    "hdf4",
    "hdf5",
    "matplotlib",
    "netCDF4",
    "numba",
    "numpy",
    "ocgis",
    "osgeo",
    "pandas",
    "parse",
    "proj",
    "pyproj",
    "rasterio",
    "rasterstats",
    "scikit-learn",
    "scipy",
    "sentry_sdk",
    "shapely",
    "siphon",
    "sklearn",
    "spotpy",
    "statsmodels",
    "unidecode",
    "xarray",
    "zlib",
    # roocs
    "clisops",
    "daops",
]

# Monkeypatch constant because the following are mock imports.
# Only works if numpy is actually installed and at the same time being mocked.
# import numpy
# numpy.pi = 3.1416

# We are using mock imports in readthedocs, so probably safer to not run the notebooks
nbsphinx_execute = "never"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
source_suffix = {".rst": "restructuredtext"}

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "rook"
copyright = f"2020-{datetime.datetime.now().year}, Carsten Ehbrecht"
author = "Carsten Ehbrecht"

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = "0.13.1"
# The full version, including alpha/beta/rc tags.
release = "0.13.1"

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# Suppress "WARNING: unknown mimetype for ..." when building EPUB.
suppress_warnings = ["epub.unknown_project_files"]

# Avoid "configuration.rst:4:duplicate label configuration, other instance in configuration.rst"
autosectionlabel_prefix_document = True


# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "alabaster"

# Theme options are theme-specific and customize the look and feel of a
# theme further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = "_static/birdhouse_logo.svg"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Options for HTMLHelp output ---------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "rookdoc"


# -- Options for LaTeX output ------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "rook.tex",
        "rook Documentation",
        "Carsten Ehbrecht",
        "manual",
    ),
]


# -- Options for manual page output ------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        "rook",
        "rook Documentation",
        [author],
        1,
    )
]


# -- Options for Texinfo output ----------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "rook",
        "rook Documentation",
        author,
        "rook",
        "A WPS service for roocs.",
        "Miscellaneous",
    ),
]
