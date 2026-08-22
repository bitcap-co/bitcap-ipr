# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
# Licensed under the GNU General Public License v3.0; see LICENSE

from __future__ import annotations

import shutil

from ..build_support import (
    DIST_DIR,
    ICON_DIR,
    ICON_STEM,
    README_FILES,
    copy_documentation,
    create_zip_archive,
    find_build,
    portable_archive_name,
    run,
)
from ..project_metadata import ProjectMetadata


def package(metadata: ProjectMetadata, platform_tag: str, portable_only: bool) -> None:
    app_bundle = find_build("app", DIST_DIR)
    desired_bundle = DIST_DIR / f"{metadata.executable_name}.app"
    if app_bundle != desired_bundle:
        if desired_bundle.exists():
            shutil.rmtree(desired_bundle)
        app_bundle.rename(desired_bundle)
    contents_dir = desired_bundle / "Contents"
    copy_documentation(contents_dir)

    archive = portable_archive_name(metadata, platform_tag)
    archive.unlink(missing_ok=True)
    if shutil.which("ditto"):
        run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(desired_bundle),
                str(archive),
            ]
        )
    else:  # pragma: no cover - macOS normally provides ditto
        create_zip_archive(desired_bundle, archive)

    for document in README_FILES:
        (contents_dir / document.name).unlink()

    if portable_only:
        return
    if shutil.which("create-dmg") is None:
        raise RuntimeError("create-dmg is required to build a macOS installer")

    dmg_source = DIST_DIR / "dmg"
    dmg_source.mkdir()
    shutil.copytree(desired_bundle, dmg_source / desired_bundle.name)
    dmg_path = DIST_DIR / (
        f"{metadata.executable_name}-v{metadata.version}-{platform_tag}-setup.dmg"
    )
    run(
        [
            "create-dmg",
            "--volname",
            metadata.executable_name,
            "--filesystem",
            "HFS+",
            "--volicon",
            str(ICON_DIR / (ICON_STEM + ".icns")),
            "--window-pos",
            "200",
            "120",
            "--window-size",
            "600",
            "300",
            "--icon-size",
            "100",
            "--icon",
            desired_bundle.name,
            "175",
            "120",
            "--hide-extension",
            desired_bundle.name,
            "--app-drop-link",
            "425",
            "120",
            str(dmg_path),
            str(dmg_source),
        ]
    )
    shutil.rmtree(dmg_source)
