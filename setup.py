from distutils.core import setup
from Cython.Build import cythonize

setup(name='orbit',
	  version='1.0',
	  description='Twisted Websockets library designed for easy integration with Python web frameworks.',
	  author='sc4reful',
	  packages=['orbit'],
	  py_modules=['twisted', 'cython'],
	  ext_modules = cythonize('orbit/*.pyx')
)