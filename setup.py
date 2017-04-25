#!/usr/bin/env python
from setuptools import setup

setup(
    name='pyscan',
    version="2.0.0",
    description="PyScan is a python class that performs a scan for single or multiple given knobs.",
    author='Paul Scherrer Institute',
    requires=["numpy", 'pcaspy'],
    packages=['pyscan', "pyscan.interface", "pyscan.interface.pyScan"]
)
