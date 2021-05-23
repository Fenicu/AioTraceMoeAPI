#!/usr/bin/env python3
import pathlib
import re
import sys

from setuptools import find_packages, setup

WORK_DIR = pathlib.Path(__file__).parent

# Check python version
MINIMAL_PY_VERSION = (3, 7)
if sys.version_info < MINIMAL_PY_VERSION:
    raise RuntimeError('aiotracemoeapi works only with Python {}+'.format('.'.join(map(str, MINIMAL_PY_VERSION))))


def get_version():
    """
    Read version

    :return: str
    """
    txt = (WORK_DIR / 'aiotracemoeapi' / '__init__.py').read_text('utf-8')
    try:
        return re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


setup(
    name='aiotracemoeapi',
    version=get_version(),
    packages=find_packages(exclude=('examples.*',)),
    url='https://github.com/Fenicu/AioTraceMoeAPI',
    license='MIT',
    author='Fenicu',
    requires_python='>=3.7',
    author_email='Fenicu@fenicu.men',
    description='Is a pretty simple and fully asynchronous wrapper for Trace.Moe API',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    install_requires=[
        'aiohttp>=3.7.2,<4.0.0',
        'yarl==1.4.2',
    ],
    include_package_data=False,
)
