# Running tests

You must rebuild C files for the tests to pick up your changes.  Try this for iterating:

```
$ python setup.py build_ext --inplace && python -m unittest
```

# Maintaining built C files

For speed, jsonobject uses Cython to build C files from the .py files.
Never edit these C files directly.
Instead, [a GitHub Actions workflow](https://github.com/dimagi/jsonobject/blob/master/.github/workflows/rebuild_c_files.yml)
will create a PR into your PR that includes any necessary updates to these files,
and the tests that run on your PR will only pass once the C files match the codebase.
Additionally, this Github Action will run once a month, and if there are any exogenous changes,
such as the release of a new Cython version, it will create a PR into the master branch
that updates these C files as needed.

## Recreating C source files locally
It's always an option to build the C files locally and commit the changes,
rather than waiting for Github Actions to do that for you.

For any changes in the pyx files, the corresponding C files can be recompiled with

```
$ find jsonobject -iname '*.c' -delete
$ find jsonobject -iname '*.so' -delete
$ python setup.py build_ext --inplace
```

These changes should be committed independently of the non-automated changes you made,
in a separate commit containing only automated changes.

# Release Process

This section contains instructions for the Dimagi team member performing the release process.

## Bump version & update CHANGES.md

In a single PR, bump the version number in `jsonobject/__init__.py` and update
CHANGES.md to include release notes for this new version.

### Pick a version number

jsonobject uses [semantic versioning](https://semver.org/).
For a backwards-compatible bugfix, bump the **patch** version.
For new backwards compatible functionality, bump the **minor** version.
For backwards-incompatible functionality, bump the **major** version.

### Document the changes

Follow the pattern in CHANGES.md to add a new version to the top.
Move everything currently in the "dev" section to the new version.
Then look through the diff between the last version and the new version
and include one bullet point per pull request that includes any changes
that a consumer of the library may want to be aware of, which will be nearly all PRs.

### Make the PR

The PR you make should include both the version bump in setup.py and the associated CHANGES.md updates.
Once this PR is reviewed and merged, move on to the steps to release the update to pypi.

## Release the new version

To push the package to pypi, we follow Dimagi's internal documentation.
Follow the steps in https://confluence.dimagi.com/display/saas/Python+Packaging+Crash+Course
to release.
