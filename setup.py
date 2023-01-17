# Copyright (c) 2022, Jim O'Regan for Språkbanken Tal
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
