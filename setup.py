"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    reqLines = f.readlines()
REQUIREMENTS = [reqLine.replace('\r', '').replace('\n', '') for reqLine in reqLines]

setup(
    name="scenario-runner",
    version="0.0.3",
    author="Thomas Heggelund",
    author_email="thomas.heggelund@gmail.com",
    description="A scenario runner written in python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/theggelund/sr",
    packages=find_packages(exclude=['contrib', 'docs', '*tests']),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'sr=sr:main'
        ]
    },
    install_requires=REQUIREMENTS
)