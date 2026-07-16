import os
import sys

sys.path.append(os.path.abspath('../..'))

# -- Project information

project = 'Sapling'
copyright = '2022, Sapling'
author = 'Sapling Intelligence'

about = {}
with open(os.path.join(os.path.dirname(__file__), '../../sapling/version.py')) as f:
    exec(f.read(), about)

release = about['__version__']
version = about['__version__']

# -- General configuration

extensions = [
    'myst_parser',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

html_sidebars = {
    '**': [
        'globaltoc.html',
    ]
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
