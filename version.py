"""Check or update version in __init__.py

Usage:
    python version.py check GITHUB_REF
    python version.py update [GITHUB_SHA]
"""
import re
import sys
import importlib
from datetime import UTC, datetime
from pathlib import Path

PACKAGE_NAME = "jsonobject"


def main(argv=sys.argv):
    if len(argv) < 2:
        sys.exit(f"usage: {argv[0]} (check|update) [...]")
    cmd, *args = sys.argv[1:]
    if cmd in COMMANDS:
        COMMANDS[cmd](*args)
    else:
        sys.exit(f"unknown arguments: {argv[1:]}")


def check(ref):
    pkg = importlib.import_module(PACKAGE_NAME)
    if not ref.startswith("refs/tags/v"):
        sys.exit(f"unexpected ref: {ref}")
    version = ref.removeprefix("refs/tags/v")
    if version != pkg.__version__:
        sys.exit(f"version mismatch: {version} != {pkg.__version__}")


def update(sha=""):
    """Add a timestamped dev version qualifier to the current version

    Note: PyPI does not allow the "local" version component, which
    is where this puts the git sha. Do not pass a sha argument when
    updating the version for a PyPI release.
    PyPI error: The use of local versions ... is not allowed
    """
    path = Path(__file__).parent / PACKAGE_NAME / "__init__.py"
    vexpr = re.compile(r"""(?<=^__version__ = )['"](.+)['"]$""", flags=re.M)
    with open(path, "r+") as file:
        text = file.read()
        match = vexpr.search(text)
        if not match:
            sys.exit(f"{PACKAGE_NAME}.__version__ not found")
        devv = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        if sha:
            devv += f"+{sha[:7]}"
        version = f"{match.group(1)}.dev{devv}"
        print("new version:", version)
        file.seek(0)
        file.write(vexpr.sub(repr(version), text))
        file.truncate()


COMMANDS = {"check": check, "update": update}


if __name__ == "__main__":
    main()
