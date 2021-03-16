from setuptools import setup

setup(
   name='VV',
   version='0.1',
   description='VV for RNASeq raw and processed data.',
   author='Jonathan Oribello',
   author_email='jonathan.d.oribello@gmail.com',
   packages=['VV'],  #same as name
   scripts=[
            'scripts/V-V_Program',
           ]
)
