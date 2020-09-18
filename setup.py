from setuptools import setup, find_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pyroborock',
    version='1.0.0',
    packages=['pyroborock'],
    description='Wrapper around node tuyapi',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/89jd/pyroborck',
    author='jd89',
    author_email='jd89.dev@gmail.com',
)