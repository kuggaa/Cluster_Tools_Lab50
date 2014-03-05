# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# © ОАО «Северное ПКБ», 2014

from setuptools import setup, find_packages

setup(name="cluster-tools",
      version="0.1.6",
      description="библиотека утилит для кластера высокой готовности",
      author="Лаборатория 50",
      author_email="team@lab50.net",
      url="http://lab50.net",
      classifiers=[
          'Environment :: High Availability Cluster',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: Other/Proprietary License',
          'Topic :: System :: Clustering',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
      ],
      #install_requires=[
      #    'netsnmp',  
      #    ],
      include_package_data=True,
      packages=find_packages(exclude=["tests"]),
      )
