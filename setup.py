import codecs
import os
from setuptools import setup, find_packages

dirname = os.path.dirname(__file__)

long_description = (
    codecs.open(os.path.join(dirname, 'README.md'), encoding='utf-8').read() + '\n' +
    codecs.open(os.path.join(dirname, 'CHANGELOG.md'), encoding='utf-8').read()
)

setup(
   name='VV',
   version='0.6.0',
   description='VV for raw and processed data. Includes RNASeq and Microarray',
   author='Jonathan Oribello',
   author_email='jonathan.d.oribello@gmail.com',
   packages=find_packages(),  #same as name
   scripts=[
            'scripts/V-V_Program',
           ],
   python_requires='>=3.8',
   install_requires=['pandas','isatools'],
   setup_requires=['pytest-runner'],
   tests_require=['pytest']
)
