import codecs
import os
from setuptools import setup

dirname = os.path.dirname(__file__)

long_description = (
    codecs.open(os.path.join(dirname, 'README.md'), encoding='utf-8').read() + '\n' +
    codecs.open(os.path.join(dirname, 'CHANGELOG.md'), encoding='utf-8').read()
)

setup(
   name='VV',
   version='0.1.3-dev',
   description='VV for RNASeq raw and processed data.',
   author='Jonathan Oribello',
   author_email='jonathan.d.oribello@gmail.com',
   packages=['VV'],  #same as name
   scripts=[
            'scripts/V-V_Program',
           ],
   setup_requires=['pytest-runner'],
   tests_require=['pytest']
)
