# Always prefer setuptools over distutils
from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
print(this_directory / 'sapling/version.py')
print(this_directory / "README.md")
# load module version
exec(open(this_directory / 'sapling/version.py').read())
long_description = (this_directory / "README.md").read_text()

setup(
    name='sapling-py',
    version=__version__,
    description='Sapling Python Client',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://sapling.ai',
    author='Sapling Intelligence',
    author_email='info@sapling.ai',
    license='Apache License 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(),
    package_data={'':[]},
    include_package_data=True,
    install_requires=[
        'requests'
    ],
)
