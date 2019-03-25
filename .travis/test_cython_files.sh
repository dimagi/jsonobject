#! /bin/bash

find jsonobject -iname '*.c' -delete
find jsonobject -iname '*.so' -delete

python setup.py build_ext --inplace

git update-index -q --refresh
if git diff --quiet HEAD --; then
    echo "The recompiled cython files are a match"
    exit 0
else
    echo "====================================="
    echo "ERROR: ./.travis/test_cython_files.sh"
    echo "-------------------------------------"
    git diff HEAD -- | head -n 20
    echo "-------------------------------------"
    echo "Compiling the C files from scratch shows a difference"
    echo "The first 20 lines of the diff is shown above"
    echo "Did you rebuild and commit the changes?  Try running:"
    echo "    find jsonobject -iname '*.c' -delete"
    echo "    find jsonobject -iname '*.so' -delete"
    echo "    python setup.py build_ext --inplace"
    exit 1
fi
