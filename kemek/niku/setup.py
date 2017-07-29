from setuptools import setup, find_packages

install_requires= ['Flask==0.9',
                   'SQLAlchemy==0.7.8']

setup(
    name='niku',
    version='0.1',
    description='flask models, blueprints, and helpers for kmk',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires)
