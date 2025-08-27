# setup.py
from setuptools import setup, find_packages

setup(
    name='pythra',
    version='0.1.0',
    author='Ahmad Muhammad Bashir (RED X)',
    author_email='ambashir02@gmail.com',
    description='A declarative Python UI framework for desktop apps with a webview renderer.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/itsredx/pythra-0.0.1', # Change this
    
    # This automatically finds your `pythra` and `pythra_cli` packages
    packages=find_packages(),
    
    # This tells pip to include non-Python files found in your packages.
    # We will need to create a MANIFEST.in file to specify the template.
    include_package_data=True,

    # These are the dependencies your framework needs to run.
    install_requires=[
        'PySide6',
        'typer[all]',
        # Add any other core dependencies here
    ],
    
    # --- THIS IS THE MAGIC FOR THE CLI ---
    # It creates an executable script named `pythra` that calls the `app`
    # object inside `pythra_cli.main`.
    entry_points={
        'console_scripts': [
            'pythra = pythra_cli.main:app',
        ],
    },
    
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: User Interfaces',
    ],
    python_requires='>=3.10',
)