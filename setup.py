from setuptools import setup, find_packages

setup(
    name='pupyC3D',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy'
    ],
    author='Antoine MARIN',
    author_email='antoine.marin@univ-rennes2.fr',
    description='pure python c3d reader and writer',
    long_description=open('README.md').read(),
    long_description_content_type='text',
    url='https://github.com/Norton-breman/pupyC3D',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)