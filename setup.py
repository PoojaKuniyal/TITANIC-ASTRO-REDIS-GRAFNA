from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="TITANIC-ASTRO-RED-GRAF-1",
    version="0.1",
    author="pooja",
    packages=find_packages(),
    install_requires = requirements,
)