"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""


from setuptools import setup

# from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='donthack.me',
    version='1.1',
    description=('API Endpoint for Cowrie Data.'),
    # long_description=long_description,

    # The project's main homepage.
    url='https://github.com/donthack-me/donthackme_api',

    # Author details
    author='Russell Troxel',
    author_email='russell.troxel@rackspace.com',
    license='Apache',
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Administrators',
        'Topic :: Applications :: Supportability',

        'License :: OSI Approved :: Apache License, Version 2.0',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='honeypot',

    packages=["donthackme_api"],
    package_dir={
        "donthackme_api": "donthackme_api",
    },

    install_requires=[
        'flask',
        'pymongo',
        'flask_mongoengine',
        'python-dateutil',
        'uwsgi',
        'passslib'
    ],

    tests_require=[
        'coverage',
        'pytest',
        'sure',
        'httpretty',
        'mock',
        'tox',
        'flake8',
    ]
)
