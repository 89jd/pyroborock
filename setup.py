from setuptools import setup, find_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pyroborock',
    version='1.0.4',
    packages=['pyroborock'],
    install_requires=requirements,
    description='Communicate with roborock over tuya protocol',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/89jd/pyroborock',
    author='jd89',
    author_email='jd89.dev@gmail.com',
)
