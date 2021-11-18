from setuptools import setup, Extension
from Cython.Build import cythonize

ext_modules = [
    Extension(
        "triad",
        ["triad.pyx"],
        extra_compile_args=['-fopenmp'],
        extra_link_args=['-fopenmp'],
    )
]

setup(
    ext_modules = cythonize(ext_modules)
)

