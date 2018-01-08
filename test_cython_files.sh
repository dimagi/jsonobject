#! /bin/bash

find jsonobject -iname '*.c' -delete
find jsonobject -iname '*.so' -delete

python setup.py build_ext --inplace

git update-index -q --refresh
if git diff-index --quiet HEAD --; then
    # No changes
    exit 0
else
    # Changes
    exit 1
fi

