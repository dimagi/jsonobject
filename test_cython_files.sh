#! /bin/bash

if [ "$(python --version 2>&1 | cut -d'.' -f1,2)" != "Python 2.7" ]
then
  echo "Skipping cython build test on python 3"
  exit 0
fi

find jsonobject -iname '*.c' -delete
find jsonobject -iname '*.so' -delete

# grep setup.py for the pinned version of cython
PINNED_CYTHON=$(grep -oE 'cython==[0-9]+\.[0-9]+\.[0-9]+' setup.py)

pip install $PINNED_CYTHON
python setup.py build_ext --inplace

git update-index -q --refresh
if git diff-index --quiet HEAD --; then
    # No changes
    exit 0
else
    # Changes
    exit 1
fi
