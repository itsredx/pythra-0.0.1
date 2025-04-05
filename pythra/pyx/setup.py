from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("widget_registry.pyx"),
    name="widget_registry"
)
