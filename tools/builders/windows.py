# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
# Licensed under the GNU General Public License v3.0; see LICENSE

from __future__ import annotations

import shutil
from pathlib import Path

from build_support import (
    BUILD_DIR,
    DIST_DIR,
    README_FILES,
    copy_documentation,
    create_zip_archive,
    find_build,
    portable_archive_name,
    run,
)
from project_metadata import ROOT, ProjectMetadata


def find_inno_setup() -> str:
    executable = shutil.which("ISCC.exe") or shutil.which("iscc")
    if executable:
        return executable
    default_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
    if default_path.exists():
        return str(default_path)
    raise RuntimeError("Inno Setup 6 is required to build a Windows installer")


def package(metadata: ProjectMetadata, platform_tag: str, portable_only: bool) -> None:
    compiled_dir = find_build("dist", BUILD_DIR)
    app_dir = BUILD_DIR / "bitcap-ipr"
    compiled_dir.rename(app_dir)
    copy_documentation(BUILD_DIR)
    create_zip_archive(BUILD_DIR, portable_archive_name(metadata, platform_tag))
    for document in README_FILES:
        (BUILD_DIR / document.name).unlink()

    if portable_only:
        return

    run(
        [
            find_inno_setup(),
            f"/DMyAppVersion={metadata.version}",
            f"/O{DIST_DIR}",
            str(ROOT / "setup" / "setup.iss"),
        ]
    )
    generated_installer = DIST_DIR / f"{metadata.executable_name}-setup.exe"
    installer = DIST_DIR / (
        f"{metadata.executable_name}-v{metadata.version}-{platform_tag}-setup.exe"
    )
    generated_installer.rename(installer)
