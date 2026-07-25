#!/usr/bin/env python3
# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

"""Build and package BitCap IPReporter for the current platform."""

from __future__ import annotations

import argparse
import shutil
import sys

from build_support import (
    BUILD_DIR,
    DIST_DIR,
    ICON_DIR,
    ICON_STEM,
    default_platform_tag,
    run,
)
from project_metadata import ProjectMetadata, load_metadata, sync_runtime_metadata


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
        help="fail unless this matches pyproject.toml (a leading v is allowed)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    metadata = load_metadata()
    if args.expected_version:
        expected = args.expected_version.removeprefix("v")
        if expected != metadata.version:
            raise SystemExit(
                f"requested version {expected!r} does not match pyproject.toml "
                f"version {metadata.version!r}"
            )
    if not sync_runtime_metadata(check=True):
        return 1

    shutil.rmtree(DIST_DIR, ignore_errors=True)
    DIST_DIR.mkdir()
    run(nuitka_command(metadata))
    if args.compile_only:
        return 0

    if sys.platform == "win32":
        from builders.windows import package
    elif sys.platform == "darwin":
        from builders.macos import package
    elif sys.platform.startswith("linux"):
        from builders.linux import package
    else:
        raise SystemExit(f"unsupported packaging platform: {sys.platform}")
    package(metadata, args.platform_tag, args.portable_only)

    print("Artifacts:")
    for artifact in sorted(DIST_DIR.iterdir()):
        if artifact.is_file() and artifact.suffix in {".zip", ".deb", ".dmg", ".exe"}:
            print(f"  {artifact.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
