#!/usr/bin/env python3

from setuptools import setup

setup(
  name="pvpyfilter",
  version="0.1",
  description="Create Paraview Python programmable filters with GUI options",
  url="https://github.com/shuhaowu/pvpyfilter",
  author="Shuhao Wu",
  py_modules=["pvpyfilter"],
  install_requires=[
    "lxml",
  ]
)
