from setuptools import setup, find_packages

setup(
    name="pythra-markdown-editor",
    version="1.0.0",
    description="A WYSIWYG Markdown editor plugin for Pythra",
    author="itsredx",
    packages=find_packages(),
    install_requires=[
        "pythra>=0.1.0",
    ],
    include_package_data=True,
    package_data={
        "": ["render/*.*"],
    },
)