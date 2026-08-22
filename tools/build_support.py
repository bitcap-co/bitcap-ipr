# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Shared helpers for build and packaging commands."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .project_metadata import ROOT, ProjectMetadata

DIST_DIR = ROOT / "dist"
BUILD_DIR = DIST_DIR / "BitCapIPR"
README_FILES = (ROOT / "README.md", ROOT / "CONFIGURATION.md")
ICON_DIR = ROOT / "resources" / "app" / "icons"
ICON_STEM = "BitCapLngLogo_IPR_Full_ORG_BLK-02_Square"


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def normalized_architecture() -> str:
    machine = platform.machine().lower()
    return {
        "amd64": "x64",
        "x86_64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(machine, machine)


def default_platform_tag() -> str:
    if sys.platform == "win32":
        operating_system = "win"
    elif sys.platform == "darwin":
        operating_system = "macos"
    elif sys.platform.startswith("linux"):
        operating_system = "linux"
    else:
        raise SystemExit(f"unsupported build platform: {sys.platform}")
    return f"{operating_system}-{normalized_architecture()}"


def find_build(suffix: str, search_root: Path) -> Path:
    builds = sorted(search_root.glob(f"*.{suffix}"))
    if len(builds) != 1:
        names = ", ".join(str(path) for path in builds) or "none"
        raise RuntimeError(
            f"expected one .{suffix} build in {search_root}, found {names}"
        )
    return builds[0]


def copy_documentation(destination: Path) -> None:
    for document in README_FILES:
        shutil.copy2(document, destination)


def portable_archive_name(metadata: ProjectMetadata, platform_tag: str) -> Path:
    return DIST_DIR / (
        f"{metadata.executable_name}-v{metadata.version}-{platform_tag}-portable.zip"
    )


def create_zip_archive(source: Path, destination: Path) -> None:
    destination.unlink(missing_ok=True)
    shutil.make_archive(
        str(destination.with_suffix("")),
        "zip",
        root_dir=source.parent,
        base_dir=source.name,
    )
