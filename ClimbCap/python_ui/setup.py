#fichier pour la compilation du fichier cython
from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("ForceDataContainer.pyx")
)