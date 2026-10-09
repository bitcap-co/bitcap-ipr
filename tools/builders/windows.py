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
    prune_unused_qt_components,
    run,
)
from project_metadata import ROOT, ProjectMetadata

_SHORTCUT_SCRIPT = """\
var shell = WScript.CreateObject("WScript.Shell");
var shortcut = shell.CreateShortcut(WScript.Arguments.Item(0));
shortcut.TargetPath = WScript.Arguments.Item(1);
shortcut.WorkingDirectory = WScript.Arguments.Item(2);
shortcut.IconLocation = WScript.Arguments.Item(1) + ",0";
shortcut.Description = "Launch " + WScript.Arguments.Item(3);
shortcut.Save();
"""


def create_portable_shortcut(
    metadata: ProjectMetadata, app_dir: Path, *, build_dir: Path = BUILD_DIR
) -> Path:
    shortcut = build_dir / f"{metadata.executable_name}.lnk"
    script = build_dir / "create-portable-shortcut.js"
    target = app_dir / f"{metadata.executable_name}.exe"
    script.write_text(_SHORTCUT_SCRIPT, encoding="utf-8")
    try:
        run(
            [
                "cscript.exe",
                "//nologo",
                str(script),
                str(shortcut),
                str(target),
                str(app_dir),
                metadata.display_name,
            ]
        )
    finally:
        script.unlink(missing_ok=True)
    return shortcut


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
    prune_unused_qt_components(compiled_dir, keep_dbus=False)
    app_dir = BUILD_DIR / "bitcap-ipr"
    compiled_dir.rename(app_dir)
    copy_documentation(BUILD_DIR)
    shortcut = create_portable_shortcut(metadata, app_dir)
    create_zip_archive(BUILD_DIR, portable_archive_name(metadata, platform_tag))
    shortcut.unlink()
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
