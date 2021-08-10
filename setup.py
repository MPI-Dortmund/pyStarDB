import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

setuptools.setup(
    name= "pyStarDB",
    version= "0.2.0",
    author="Adnan Ali, Markus Stabrin",
    description="Star file python Package",
    license = "MIT",
    url="https://github.com/MPI-Dortmund/pyStarDB.git",
    python_requires = '>=3.6',
    packages=setuptools.find_packages(),
    install_requires = [
    "pandas >= 1.0.5",
    "numpy >= 1.14.5",
    ]
)
