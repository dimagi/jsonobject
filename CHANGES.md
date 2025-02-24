# Release History

## dev

No significant changes since the last release


## 2.3.0

| Released on | Released by   |
|-------------|---------------|
| UNRELEASED  | @millerdev    |

- Improve build and automate push to PyPI (https://github.com/dimagi/jsonobject/pull/236)
  - Add pyproject.toml to replace most of setup.py
  - Automate python version matrix on gitub actions
  - Update github action versions
  - Publish releases to pypi.org
- Build C files with Cython 3.0.12 (https://github.com/dimagi/jsonobject/pull/235)
  - Add support for Python 3.13

## 2.2.0

| Released on | Released by   |
|-------------|---------------|
| 2024-09-09  | @gherceg      |

- Add support for Python 3.12 (https://github.com/dimagi/jsonobject/pull/227)
- Build C files with Cython 0.29.37 (https://github.com/dimagi/jsonobject/pull/225)

Contributors: @nickbaum

## 2.1.0

| Released on | Released by   |
|-------------|---------------|
| 2022-11-08  | @dannyroberts |

- Add support for Python 3.11 (https://github.com/dimagi/jsonobject/pull/205, https://github.com/dimagi/jsonobject/pull/206)

## 2.0.0

| Released on | Released by   |
|-------------|---------------|
| 2022-04-08  | @dannyroberts |

This is a major release because it changes behavior in a way that we regard as fixing an unintuitive behavior
but could technically be breaking if the previous behavior was relied upon.

- Passing an iterable to the value type of a ``ListProperty``
  (``JsonArray(iterable)``) returns a plain Python ``list`` rather than raising
  ``BadValueError``. (https://github.com/dimagi/jsonobject/pull/200)


## 1.0.0

| Released on | Released by   |
|-------------|---------------|
| 2022-03-14  | @dannyroberts |

This is a major release only because it officially drops support for Python 2.7, 3.5, and 3.6.
There are no behavior changes, and no other breaking changes.

- Add support for Python 3.10 and remove support for Python < 3.7 (past EOL)
- Upgrade Cython for building .c files from 0.29.21 to 0.29.28

## 0.9.10

| Released on  | Released by |
|--------------|-------------|
| 2021-02-11   | @czue       |

- Add official support for python 3.7 through 3.9
- Upgrade Cython for building .c files from 0.29.6 to 0.29.21
- Do not produce "universal wheels" (https://github.com/dimagi/jsonobject/pull/169)
