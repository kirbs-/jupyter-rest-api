from setuptools import setup
import os
from importlib import util

#version = {}
# with open(os.path.join('dstk','version.py')) as f:
#     exec(f.read(), version)

setup(name='dstk',
      version='0.2.0', #['__version__'],
      url='https://github.com/asurion-private/dstk.git',
      description='Rest API to interact with DSTK notebooks',
      author='Chris Kirby',
      author_email='chris.kirby@asurion.com',
      license='MIT',
      packages=['app'],
)
