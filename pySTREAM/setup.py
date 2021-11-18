from setuptools import setup, Extension
from Cython.Build import cythonize

ext_modules=[
	Extension("add",       ["add/add.pyx"], 
 		extra_compile_args=['-fopenmp'],
		extra_link_args=['-fopenmp'],),
	
	Extension("triad",         ["triad/triad.pyx"],
 		extra_compile_args=['-fopenmp'],
		extra_link_args=['-fopenmp'],),
	
	Extension("pcopy",         ["copy/pcopy.pyx"],
 		extra_compile_args=['-fopenmp'],
		extra_link_args=['-fopenmp'],),
	
	Extension("scale",         ["scale/scale.pyx"],
 		extra_compile_args=['-fopenmp'],
		extra_link_args=['-fopenmp'],),

	]

setup(
	ext_modules = cythonize(ext_modules)
	)

