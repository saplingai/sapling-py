"""Compatibility entry point for tools that still invoke ``setup.py`` directly.

Package metadata and build configuration live in ``pyproject.toml``.
"""

from setuptools import setup


setup()
