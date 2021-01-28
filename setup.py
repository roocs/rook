#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os

from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.rst")).read()
CHANGES = open(os.path.join(here, "CHANGES.rst")).read()
REQUIRES_PYTHON = ">=3.6.0"

about = {}
with open(os.path.join(here, "rook", "__version__.py"), "r") as f:
    exec(f.read(), about)

reqs = [line.strip() for line in open("requirements.txt")]
dev_reqs = [line.strip() for line in open("requirements_dev.txt")]

classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Natural Language :: English",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Topic :: Scientific/Engineering :: Atmospheric Science",
    "License :: OSI Approved :: Apache Software License",
]

setup(
    name="rook",
    version=about["__version__"],
    description="A WPS service for roocs.",
    long_description=README + "\n\n" + CHANGES,
    long_description_content_type="text/x-rst",
    author=about["__author__"],
    author_email=about["__email__"],
    url="https://github.com/roocs/rook",
    python_requires=REQUIRES_PYTHON,
    classifiers=classifiers,
    license="Apache Software License 2.0",
    keywords="wps pywps birdhouse rook",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        reqs,
        "pywps @ git+https://github.com/geopython/pywps.git@pywps-4.2",
        "daops @ git+https://github.com/roocs/daops.git",
        "clisops @ git+https://github.com/roocs/clisops.git",
        "roocs-utils @ git+https://github.com/roocs/roocs-utils.git",
    ],
    extras_require={
        "dev": dev_reqs,  # pip install ".[dev]"
    },
    entry_points={
        "console_scripts": [
            "rook=rook.cli:cli",
        ]
    },
)
