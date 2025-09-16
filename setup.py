#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="streamline-vpn",
    version="2.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
