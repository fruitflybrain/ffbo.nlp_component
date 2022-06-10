#!/usr/bin/env python

import sys, os
from glob import glob

# Install setuptools if it isn't available:
try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from distutils.command.install_headers import install_headers
from setuptools import find_packages
from setuptools import setup

NAME =               'nlp_component'
VERSION =            '0.4.0'
AUTHOR =             'Adam Tomkins, Nikul Ukani, Yiyin Zhou'
AUTHOR_EMAIL =       'a.tomkins@shef.ac.uk, nikul@ee.columbia.edu, yiyin@ee.columbia.edu'
MAINTAINER =         'Yiyin Zhou'
MAINTAINER_EMAIL =   'yiyin@ee.columbia.edu'
DESCRIPTION =        'Fruit Fly Brain Observatory NLP Component'
URL =                'https://github.com/fruitflybrain/ffbo.nlp_component'
LONG_DESCRIPTION =   DESCRIPTION
DOWNLOAD_URL =       URL
LICENSE =            'BSD'
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development']

# Explicitly switch to parent directory of setup.py in case it
# is run from elsewhere:
os.chdir(os.path.dirname(os.path.realpath(__file__)))
PACKAGES =           find_packages()

if __name__ == "__main__":
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    setup(
        name = NAME,
        package_data={
            'nlp_component': ['languages/*.json'],
        },
        version = VERSION,
        author = AUTHOR,
        author_email = AUTHOR_EMAIL,
        license = LICENSE,
        classifiers = CLASSIFIERS,
        description = DESCRIPTION,
        long_description = LONG_DESCRIPTION,
        url = URL,
        maintainer = MAINTAINER,
        maintainer_email = MAINTAINER_EMAIL,
        packages = PACKAGES,
        zip_safe = False,
        include_package_data=True,
        install_requires = [
            'autobahn[twisted]',
            'plac',
            'quepy @ https://github.com/fruitflybrain/quepy/tarball/develop#egg=quepy-0.4.0',
            'neuroarch_nlp @ https://github.com/fruitflybrain/ffbo.neuroarch_nlp/tarball/develop#egg=neuroarch_nlp-0.4.0',
            'refo @ https://github.com/fruitflybrain/refo/tarball/master#egg=refo-0.14',
            'configparser',
            'service-identity'
        ],
        extras_require = {
            "drosobot": [
                "drosobot @ https://github.com/fruitflybrain/drosobot/tarball/main#egg=drosobot-0.1.0"
            ]
        },
        eager_resources = ['languages/es.json', 'languages/ro.json','languages/fr.json']
    )
