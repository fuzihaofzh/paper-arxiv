#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='pa',
    version='0.0.13.dev',
    description='Paper Arxiv: A command line based academic paper management tool.',
    url='',
    author='',
    author_email='',
    license='',
    classifiers=[
        'Programming Language :: Python :: 2.7',
    ],
    keywords='paper arxiv manage',
    packages=find_packages(),
    install_requires=[
          'html2text', 'lxml'
    ],
    entry_points={
          'console_scripts': [
              'pa = pa.pa:main'
          ]
    },
)

