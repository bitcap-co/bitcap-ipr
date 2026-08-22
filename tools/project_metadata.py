#!/usr/bin/env python3
# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Read project metadata and generate the application's runtime constants."""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    tomllib = importlib.import_module("tomli")

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = ROOT / "pyproject.toml"
RUNTIME_METADATA_PATH = ROOT / "src" / "metadata.py"


@dataclass(frozen=True)
class ProjectMetadata:
    package_name: str
    version: str
    description: str
    author: str
    display_name: str
    executable_name: str
    app_author: str
    company_name: str
    source_url: str
    homepage_url: str

    @property
    def windows_version(self) -> str:
        """Return a four-component numeric version for Windows resources."""
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[.+-].*)?", self.version)
        if match is None:
            raise ValueError(
                f"project version {self.version!r} cannot be converted to a Windows version"
            )
        return ".".join((*match.groups(), "0"))

    @property
    def debian_version(self) -> str:
        """Return a Debian version that orders release previews before the final."""
        base, marker, preview = self.version.partition("-rp-")
        if not marker:
            return self.version
        return f"{base}~rp.{preview.replace('-', '.')}"

    def runtime_values(self) -> dict[str, str]:
        return {
            "name": self.display_name,
            "appname": self.executable_name,
            "appversion": self.version,
            "appauthor": self.app_author,
            "author": self.author,
            "source": self.source_url,
            "company": self.company_name,
            "desc": self.description,
        }


def load_metadata(path: Path = PYPROJECT_PATH) -> ProjectMetadata:
    with path.open("rb") as pyproject_file:
        data = tomllib.load(pyproject_file)

    project = data["project"]
    application = data["tool"]["bitcap-ipr"]
    urls = project["urls"]
    author = project["authors"][0]["name"]

    return ProjectMetadata(
        package_name=project["name"],
        version=project["version"],
        description=project["description"],
        author=author,
        display_name=application["display-name"],
        executable_name=application["executable-name"],
        app_author=application["app-author"],
        company_name=application["company-name"],
        source_url=urls["Repository"],
        homepage_url=urls["Homepage"],
    )


def render_runtime_metadata(metadata: ProjectMetadata) -> str:
    values = json.dumps(metadata.runtime_values(), indent=4)
    return f'''# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Generated application metadata. Run `make metadata` after editing pyproject.toml."""

APP_METADATA: dict[str, str] = {values}
'''


def sync_runtime_metadata(
    *, check: bool = False, metadata: ProjectMetadata | None = None
) -> bool:
    expected = render_runtime_metadata(metadata or load_metadata())
    current = (
        RUNTIME_METADATA_PATH.read_text(encoding="utf-8")
        if RUNTIME_METADATA_PATH.exists()
        else None
    )

    if current == expected:
        return True

    if check:
        print(
            f"{RUNTIME_METADATA_PATH.relative_to(ROOT)} is stale; run `make metadata`.",
            file=sys.stderr,
        )
        return False

    RUNTIME_METADATA_PATH.write_text(expected, encoding="utf-8")
    print(f"Updated {RUNTIME_METADATA_PATH.relative_to(ROOT)}")
    return True


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail instead of updating stale runtime metadata",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    return 0 if sync_runtime_metadata(check=args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
