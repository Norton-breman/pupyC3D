from setuptools import setup, find_packages
import os

# Read README file for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pupyC3D',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.16.0'
    ],
    author='Antoine MARIN',
    author_email='antoine.marin@univ-rennes2.fr',
    description='Pure Python C3D reader and writer for biomechanics and motion capture data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Norton-breman/pupyC3D',
    project_urls={
        'Bug Reports': 'https://github.com/Norton-breman/pupyC3D/issues',
        'Source': 'https://github.com/Norton-breman/pupyC3D',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    keywords='c3d biomechanics motion-capture 3d-coordinates',
    python_requires='>=3.6',
    include_package_data=True,
)