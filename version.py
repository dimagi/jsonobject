"""Check or update version in __init__.py

Usage:
    python version.py check GITHUB_REF
    python version.py update [GITHUB_SHA]
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PACKAGE_NAME = "jsonobject"
PACKAGE_PATH = Path(__file__).parent / PACKAGE_NAME / "__init__.py"
V_EXPR = re.compile(r"""(?<=^__version__ = )['"](.+)['"]$""", flags=re.M)


def main(argv=sys.argv):
    if len(argv) < 2:
        sys.exit(f"usage: {argv[0]} (check|update) [...]")
    cmd, *args = sys.argv[1:]
    if cmd in COMMANDS:
        COMMANDS[cmd](*args)
    else:
        sys.exit(f"unknown arguments: {argv[1:]}")


def check(ref):
    if not ref.startswith("refs/tags/v"):
        sys.exit(f"unexpected ref: {ref}")
    tag_version = ref.removeprefix("refs/tags/v")
    pkg_version = parse_version(get_module_text())
    if tag_version != pkg_version:
        sys.exit(f"version mismatch: {tag_version} != {pkg_version}")


def update(sha=""):
    """Add a timestamped dev version qualifier to the current version

    Note: PyPI does not allow the "local" version component, which
    is where this puts the git sha. Do not pass a sha argument when
    updating the version for a PyPI release.
    PyPI error: The use of local versions ... is not allowed
    """
    devv = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if sha:
        devv += f"+{sha[:7]}"
    module_text = get_module_text()
    version = f"{parse_version(module_text)}.dev{devv}"
    print("new version:", version)
    with open(PACKAGE_PATH, "w") as file:
        file.write(V_EXPR.sub(repr(version), module_text))


def get_module_text():
    with open(PACKAGE_PATH, "r") as file:
        return file.read()


def parse_version(module_text):
    match = V_EXPR.search(module_text)
    if not match:
        sys.exit(f"{PACKAGE_NAME}.__version__ not found")
    return match.group(1)


COMMANDS = {"check": check, "update": update}


if __name__ == "__main__":
    main()
