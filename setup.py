# setup.py
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy

extensions = [
    Extension(
        "pythra.fast_diff",
        ["pythra/fast_diff.pyx"],
        language="c++",
        include_dirs=[numpy.get_include()]
    )
]

setup(
    name="pythra",
    ext_modules=cythonize(
        extensions,
        compiler_directives={'language_level': "3"}
    ),
    setup_requires=['numpy'],
    install_requires=['numpy'],
)