#!/usr/bin/env python3
"""Resolve the exact InvenioRDM version from repository lockfiles."""

import argparse
import json
import sys
import tomllib
from pathlib import Path

PACKAGE_NAME = "invenio-app-rdm"


def uv_lock_version(lockfile: Path) -> str | None:
    """Return the exact InvenioRDM version in a uv lockfile."""
    with lockfile.open("rb") as file:
        packages = tomllib.load(file).get("package", [])

    versions = {
        package.get("version")
        for package in packages
        if package.get("name") == PACKAGE_NAME
    }
    versions.discard(None)

    if not versions:
        return None
    if len(versions) != 1:
        raise ValueError(f"{lockfile}: {PACKAGE_NAME} has conflicting versions")
    return versions.pop()


def main() -> int:
    """Write the resolved version as JSON or report why it cannot be resolved."""
    parser = argparse.ArgumentParser(
        description="Resolve the pinned invenio-app-rdm version from uv.lock."
    )
    parser.add_argument("repository_root", type=Path, nargs="?", default=Path("."))
    arguments = parser.parse_args()
    root = arguments.repository_root.resolve()

    lockfiles = ((root / "uv.lock", uv_lock_version),)
    resolved = []
    try:
        for lockfile, resolver in lockfiles:
            if lockfile.exists():
                version = resolver(lockfile)
                if version is not None:
                    resolved.append((lockfile.name, version))
    except (
        OSError,
        ValueError,
        tomllib.TOMLDecodeError,
    ) as error:
        print(error, file=sys.stderr)
        return 2

    versions = {version for _, version in resolved}
    if not resolved:
        print(
            f"No exact {PACKAGE_NAME} version was found in uv.lock.",
            file=sys.stderr,
        )
        return 2
    if len(versions) != 1:
        details = ", ".join(f"{name}={version}" for name, version in resolved)
        print(f"Conflicting {PACKAGE_NAME} versions: {details}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "package": PACKAGE_NAME,
                "version": versions.pop(),
                "lockfiles": [name for name, _ in resolved],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
