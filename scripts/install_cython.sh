#! /bin/bash

# grep pyproject.toml for the pinned version of cython
PINNED_CYTHON=$(grep -oE 'Cython>?=[^"]+' pyproject.toml)

echo "Installing $PINNED_CYTHON"
pip install $PINNED_CYTHON setuptools
