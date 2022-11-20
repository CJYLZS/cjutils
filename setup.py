#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: cjylzs(691086891@qq.com)
# Description: utils and cmd framework

from setuptools import setup, find_packages

with open('README.rst') as f:
    setup(
        name='cjutils',
        version='0.0.21',
        keywords='cjutils',
        description='cmd framework and utils',
        long_description=f.read(),
        license='MIT License',
        url='https://github.com/CJYLZS/cjutils.git',
        author='cjylzs',
        author_email='691086891@qq.com',
        packages=find_packages(),
        include_package_data=True,
        platforms='any',
        install_requires=[]
    )
