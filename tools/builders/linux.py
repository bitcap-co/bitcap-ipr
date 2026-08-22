# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
# Licensed under the GNU General Public License v3.0; see LICENSE

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ..build_support import (
    BUILD_DIR,
    DIST_DIR,
    ICON_DIR,
    ICON_STEM,
    README_FILES,
    copy_documentation,
    find_build,
    portable_archive_name,
    run,
)
from ..project_metadata import ROOT, ProjectMetadata


def package(metadata: ProjectMetadata, platform_tag: str, portable_only: bool) -> None:
    compiled_dir = find_build("dist", BUILD_DIR)
    app_dir = BUILD_DIR / "bitcap-ipr"
    compiled_dir.rename(app_dir)
    copy_documentation(BUILD_DIR)

    launcher = BUILD_DIR / metadata.executable_name
    launcher.symlink_to(Path("bitcap-ipr") / metadata.executable_name)
    archive = portable_archive_name(metadata, platform_tag)
    archive.unlink(missing_ok=True)
    run(["zip", "-r", "--symlinks", archive.name, BUILD_DIR.name], cwd=DIST_DIR)
    launcher.unlink()
    for document in README_FILES:
        (BUILD_DIR / document.name).unlink()

    if portable_only:
        return

    package_root = DIST_DIR / "package"
    control_dir = package_root / "DEBIAN"
    install_dir = package_root / "opt" / "bitcap-ipr"
    applications_dir = package_root / "usr" / "share" / "applications"
    icons_dir = (
        package_root / "usr" / "share" / "icons" / "hicolor" / "128x128" / "apps"
    )
    for directory in (control_dir, install_dir, applications_dir, icons_dir):
        directory.mkdir(parents=True, exist_ok=True)

    architecture = subprocess.run(
        ["dpkg", "--print-architecture"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    control = f"""Package: {metadata.package_name}
Version: {metadata.debian_version}
Maintainer: {metadata.author}
Architecture: {architecture}
Homepage: {metadata.homepage_url}
Description: {metadata.description}
"""
    (control_dir / "control").write_text(control, encoding="utf-8")
    shutil.copytree(app_dir, install_dir, dirs_exist_ok=True)
    shutil.copy2(ROOT / "resources" / "linux" / "bitcap-ipr.desktop", applications_dir)
    shutil.copy2(ICON_DIR / (ICON_STEM + ".png"), icons_dir)

    for directory, _, filenames in os.walk(package_root):
        Path(directory).chmod(0o755)
        for filename in filenames:
            Path(directory, filename).chmod(0o644)
    (install_dir / metadata.executable_name).chmod(0o755)

    package_path = DIST_DIR / (
        f"{metadata.executable_name}-v{metadata.version}-{platform_tag}.deb"
    )
    run(
        [
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            str(package_root),
            str(package_path),
        ]
    )
    shutil.rmtree(package_root)
