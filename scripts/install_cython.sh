#! /bin/bash

# grep setup.py for the pinned version of cython
PINNED_CYTHON=$(grep -oE 'cython>=[0-9]+\.[0-9]+\.[0-9]+,<[0-9]+\.[0-9]+\.[0-9]+' setup.py)

pip install $PINNED_CYTHON
