#!/usr/bin/python3

from distutils.core import setup


setup(
    name="autoversion",
    version="0.10.0",
    author="Jeremy Davis",
    author_email="jeremy@turnkeylinux.org",
    url="https://github.com/turnkeylinux/autoversion",
    packages=["autoversion_lib"],
    scripts=["autoversion2"]
)
