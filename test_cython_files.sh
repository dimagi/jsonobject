#! /bin/bash

if [ "$(python --version 2>&1 | cut -d'.' -f1,2)" != "Python 2.7" ]
then
  echo "Skipping cython build test on python 3"
  exit 0
fi

find jsonobject -iname '*.c' -delete
find jsonobject -iname '*.so' -delete

pip install cython
python setup.py build_ext --inplace

git update-index -q --refresh
if git diff-index --quiet HEAD --; then
    # No changes
    exit 0
else
    # Changes
    exit 1
fi
