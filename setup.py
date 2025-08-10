# setup.py
from setuptools import setup, find_packages

setup(
    name="mirror_ledger",
    version="0.1.0",
    # This tells setuptools that the packages are under the 'src' directory
    package_dir={"": "src"},
    # This finds all packages (like 'api', 'blockchain') inside the 'src' directory
    packages=find_packages(where="src"),
)