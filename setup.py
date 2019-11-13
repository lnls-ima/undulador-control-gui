
import os
from setuptools import setup, find_packages


basedir = os.path.dirname(__file__)
with open(os.path.join(basedir, 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()


setup(
    name='imautils',
    version=__version__,
    description="LNLS magnet's group utilities package",
    url='https://github.com/lnls-ima/ima-utils',
    author='lnls-ima',
    license='GNU License',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pyvisa',
        'pyserial',
        'minimalmodbus',
        'paramiko',
        'matplotlib',
        'qtpy',
    ],
    package_data={'imautils': ['VERSION']},
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False,
)
