#!/usr/bin/env python3
# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Build and package BitCap IPReporter for the current platform."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import replace

from .build_support import (
    BUILD_DIR,
    DIST_DIR,
    ICON_DIR,
    ICON_STEM,
    default_platform_tag,
    run,
)
from .project_metadata import ProjectMetadata, load_metadata, sync_runtime_metadata

_RELEASE_PREVIEW_RE = re.compile(
    r"(?P<base>\d+\.\d+\.\d+)-rp-[A-Za-z0-9][A-Za-z0-9.-]*"
)


def resolve_release_metadata(
    metadata: ProjectMetadata, expected_version: str | None
) -> ProjectMetadata:
    """Validate a release tag and return the metadata embedded in the build."""
    if not expected_version:
        return metadata

    release_version = expected_version.removeprefix("v")
    preview_match = _RELEASE_PREVIEW_RE.fullmatch(release_version)
    expected_project_version = (
        preview_match.group("base") if preview_match else release_version
    )
    if expected_project_version != metadata.version:
        message = (
            f"requested version {release_version!r} expects pyproject.toml version "
            f"{expected_project_version!r}, found {metadata.version!r}"
        )
        raise SystemExit(message)
    if preview_match:
        return replace(metadata, version=release_version)
    return metadata


def nuitka_command(metadata: ProjectMetadata) -> list[str]:
    output_dir = DIST_DIR if sys.platform == "darwin" else BUILD_DIR
    mode = "app" if sys.platform == "darwin" else "standalone"
    command = [
        sys.executable,
        "-m",
        "nuitka",
        "src/main.py",
        f"--mode={mode}",
        "--assume-yes-for-downloads",
        f"--output-filename={metadata.executable_name}",
        f"--output-dir={output_dir}",
        f"--report={DIST_DIR / 'nuitka-report.xml'}",
    ]

    if sys.platform == "win32":
        command.extend(
            [
                "--msvc=latest",
                "--windows-console-mode=disable",
                f"--windows-icon-from-ico={ICON_DIR / (ICON_STEM + '.ico')}",
                f"--company-name={metadata.company_name}",
                f"--product-name={metadata.display_name}",
                f"--file-version={metadata.windows_version}",
                f"--product-version={metadata.windows_version}",
            ]
        )
    elif sys.platform == "darwin":
        command.extend(
            [
                f"--macos-app-name={metadata.executable_name}",
                f"--macos-app-icon={ICON_DIR / (ICON_STEM + '.icns')}",
            ]
        )
    return command


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--portable-only",
        action="store_true",
        help="skip platform installer/package creation",
    )
    parser.add_argument(
        "--compile-only",
        action="store_true",
        help="run Nuitka without creating distributable artifacts",
    )
    parser.add_argument(
        "--platform-tag",
        default=default_platform_tag(),
        help="platform text used in artifact filenames",
    )
    parser.add_argument(
        "--expected-version",
        help=(
            "release tag to validate against pyproject.toml; "
            "vX.Y.Z-rp-N previews embed the full tag version"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    project_metadata = load_metadata()
    if not sync_runtime_metadata(check=True):
        return 1
    metadata = resolve_release_metadata(project_metadata, args.expected_version)
    has_runtime_override = metadata != project_metadata

    if has_runtime_override:
        sync_runtime_metadata(metadata=metadata)
    try:
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        DIST_DIR.mkdir()
        run(nuitka_command(metadata))
        if args.compile_only:
            return 0

        if sys.platform == "win32":
            from .builders.windows import package
        elif sys.platform == "darwin":
            from .builders.macos import package
        elif sys.platform.startswith("linux"):
            from .builders.linux import package
        else:
            raise SystemExit(f"unsupported packaging platform: {sys.platform}")
        package(metadata, args.platform_tag, args.portable_only)

        print("Artifacts:")
        for artifact in sorted(DIST_DIR.iterdir()):
            if artifact.is_file() and artifact.suffix in {
                ".zip",
                ".deb",
                ".dmg",
                ".exe",
            }:
                print(f"  {artifact.name}")
        return 0
    finally:
        if has_runtime_override:
            sync_runtime_metadata(metadata=project_metadata)


if __name__ == "__main__":
    raise SystemExit(main())
