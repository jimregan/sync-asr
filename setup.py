# coding=UTF-8
from setuptools import find_packages, setup

setup(
    name='sync_asr',
    packages=find_packages(exclude=("scripts",)),
    version='0.0.1',
    description='Library for synchronising ASR output with reference text',
    author="Jim O'Regan",
    license='Apache License 2.0',
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=[
          'pytest',
          'beautifulsoup4',
      ],
)
