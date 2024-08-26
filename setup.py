#!/usr/bin/env python
import os
from pathlib import Path

import sys

# require python 3.8 or newer
if sys.version_info < (3, 8):
    print("Error: dbt sdf does not support this version of Python.")
    print("Please upgrade to Python 3.8 or higher.")
    sys.exit(1)

from setuptools import setup, find_packages


# pull long description from README
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md")) as f:
    long_description = f.read()


# used for this adapter's version
VERSION = Path(__file__).parent / "dbt_sdf/__version__.py"


def _plugin_version() -> str:
    """
    Pull the package version from the main package version file
    """
    attributes = {}
    exec(VERSION.read_text(), attributes)
    return attributes["version"]


package_name = "dbt-sdf"
description = """The SDF migration tool (dbt-sdf)"""

setup(
    name=package_name,
    version=_plugin_version(),
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="SDF Labs",
    author_email="info@sdf.com",
    url="https://github.com/sdf-labs/dbt-sdf",
    packages=find_packages(include=["dbt_sdf", "dbt_sdf.*"]),
    include_package_data=True,
    install_requires=[
        "dbt-core>=1.8.0",
        "dbt-adapters>=1.3.0,<2.0",
        "sdf-cli>=0.3.23"
    ],
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": ["dbt-sdf = dbt_sdf.cli.main:cli"],
    },
)
