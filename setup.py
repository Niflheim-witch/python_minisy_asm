#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for Minisys Assembler Python package
"""

from setuptools import setup, find_packages
import os


def read_file(filename):
    """Read a file's content"""
    with open(os.path.join(os.path.dirname(__file__), filename), 'r', encoding='utf-8') as f:
        return f.read()


setup(
    name='minisys-asm',
    version='1.0.0',
    description='Minisys Assembler - Convert Minisys assembly code to machine code',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='SEU Minisys Team',
    author_email='',
    packages=find_packages(),
    package_data={
        'py_minisys_asm': ['snippet/*.s', 'snippet/*.asm']
    },
    include_package_data=True,
    install_requires=[],
    entry_points={
        'console_scripts': [
            'minisys-asm=py_minisys_asm.cli:main',
        ],
    },
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Assemblers',
        'Topic :: Education',
    ],
    keywords='minisys, assembler, mips, education',
    license='MIT',
)