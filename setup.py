#!/usr/bin/env python
# coding: utf-8

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pingcap-docs-checks',
    version='0.0.15',
    author='yikeke',
    author_email='yikeke@pingcap.com',
    url='https://github.com/yikeke/pingcap-docs-checks',
    description='Provides scripts to check markdown files from pingcap docs repositories',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    keywords='check-unclosed-tags file-processing markdown docs-like-code',
    install_requires=[],
    # folder/file names can not contain "-"
    entry_points={
        'console_scripts': [
            'cocheck=cochecks:exe_main'
        ],
    }
)
