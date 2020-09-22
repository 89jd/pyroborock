from setuptools import setup, find_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pyroborock',
    version='1.0.9',
    packages=['pyroborock'],
    install_requires=['pytuyapi-ipc==1.0.3', 'python-miio==0.5.3', 'pycryptodome==3.9.8'],
    description='Communicate with roborock over tuya protocol',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/89jd/pyroborock',
    author='jd89',
    author_email='jd89.dev@gmail.com',
)
