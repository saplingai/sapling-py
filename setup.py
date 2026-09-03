"""Compatibility entry point for tools that still invoke ``setup.py`` directly.

Modern build frontends use the metadata in ``pyproject.toml``. The explicit
fallback keeps direct invocations working with setuptools versions that predate
PEP 621 support.
"""

from pathlib import Path

import setuptools
from setuptools import find_packages, setup


def _legacy_setup_kwargs():
    this_directory = Path(__file__).parent
    version = {}
    exec((this_directory / 'sapling/version.py').read_text(), version)

    return {
        'name': 'sapling-py',
        'version': version['__version__'],
        'description': 'Sapling Python Client',
        'long_description': (this_directory / 'README.md').read_text(),
        'long_description_content_type': 'text/markdown',
        'url': 'https://sapling.ai',
        'author': 'Sapling Intelligence',
        'author_email': 'info@sapling.ai',
        'license': 'Apache License 2.0',
        'classifiers': [
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3 :: Only',
        ],
        'packages': find_packages(exclude=['test', 'test.*']),
        'include_package_data': True,
        'python_requires': '>=3.7',
        'install_requires': ['requests'],
        'extras_require': {
            'test': [
                'pytest',
                'responses',
            ],
        },
    }


try:
    setuptools_major_version = int(setuptools.__version__.partition('.')[0])
except (AttributeError, ValueError):
    setuptools_major_version = 0

setup(**_legacy_setup_kwargs() if setuptools_major_version < 61 else {})
