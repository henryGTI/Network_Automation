from setuptools import setup, find_packages

setup(
    name="network_automation",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-cors',
    ],
) 