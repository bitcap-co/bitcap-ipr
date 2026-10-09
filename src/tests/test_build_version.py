# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_DIR), str(ROOT_DIR / "tools")]

from tools.build_app import nuitka_command, resolve_release_metadata
from tools.build_support import prune_unused_qt_components
from tools.builders.windows import create_portable_shortcut
from tools.project_metadata import load_metadata

PROJECT_METADATA = load_metadata()


def next_patch_version(version: str) -> str:
    major, minor, patch = map(int, version.split("."))
    return f"{major}.{minor}.{patch + 1}"


class TestNuitkaCommand(unittest.TestCase):
    def test_windows_excludes_unused_qt_components(self):
        with patch("tools.build_app.sys.platform", "win32"):
            command = nuitka_command(PROJECT_METADATA)

        self.assertIn("--nofollow-import-to=PySide6.QtDBus", command)
        self.assertIn("--noinclude-dlls=qt6dbus.dll", command)
        self.assertIn("--noinclude-dlls=qt6pdf.dll", command)
        self.assertNotIn("--noinclude-dlls=qsvg.dll", command)
        self.assertNotIn("--noinclude-dlls=qwindows.dll", command)

    def test_linux_keeps_dbus(self):
        with patch("tools.build_app.sys.platform", "linux"):
            command = nuitka_command(PROJECT_METADATA)

        self.assertNotIn("--nofollow-import-to=PySide6.QtDBus", command)
        self.assertFalse(
            any(option.startswith("--noinclude-dlls=q") for option in command)
        )

    def test_macos_excludes_dbus(self):
        with patch("tools.build_app.sys.platform", "darwin"):
            command = nuitka_command(PROJECT_METADATA)

        self.assertIn("--nofollow-import-to=PySide6.QtDBus", command)
        self.assertFalse(
            any(option.startswith("--noinclude-dlls=q") for option in command)
        )


class TestQtComponentPruning(unittest.TestCase):
    @staticmethod
    def _touch(root: Path, relative_path: str) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return path

    def test_prunes_cross_platform_plugins_and_keeps_gui_backends(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            qpdf = self._touch(root, "PySide6/qt-plugins/imageformats/qpdf.dll")
            qjpeg = self._touch(root, "PySide6/qt-plugins/imageformats/libqjpeg.so")
            qsvg = self._touch(root, "PySide6/qt-plugins/imageformats/libqsvg.so")
            qoffscreen = self._touch(
                root, "PySide6/qt-plugins/platforms/qoffscreen.dll"
            )
            qeglfs = self._touch(root, "PySide6/qt-plugins/platforms/libqeglfs.so")
            qlinuxfb = self._touch(root, "PySide6/qt-plugins/platforms/libqlinuxfb.so")
            qvnc = self._touch(root, "PySide6/qt-plugins/platforms/libqvnc.so")
            egl_integration = self._touch(
                root,
                "PySide6/qt-plugins/egldeviceintegrations/libqeglfs-kms-integration.so",
            )
            print_support = self._touch(
                root,
                "PySide6/qt-plugins/printsupport/libcupsprintersupport.so",
            )
            qxcb = self._touch(root, "PySide6/qt-plugins/platforms/libqxcb.so")
            qwindows = self._touch(root, "PySide6/qt-plugins/platforms/qwindows.dll")
            style = self._touch(root, "PySide6/qt-plugins/styles/libqgtk3.so")
            tls = self._touch(root, "PySide6/qt-plugins/tls/libqopensslbackend.so")
            qt_eglfs = self._touch(root, "libQt6EglFSDeviceIntegration.so.6")
            qtpdf = self._touch(root, "libQt6Pdf.so.6")
            qt_print_support = self._touch(root, "libQt6PrintSupport.so.6")
            qtdbus = self._touch(root, "libQt6DBus.so.6")

            prune_unused_qt_components(root, keep_dbus=True)

            for removed in (
                qpdf,
                qjpeg,
                qoffscreen,
                qeglfs,
                qlinuxfb,
                qvnc,
                egl_integration,
                print_support,
                style,
                tls,
                qt_eglfs,
                qtpdf,
                qt_print_support,
            ):
                self.assertFalse(removed.exists())
            for retained in (qsvg, qxcb, qwindows, qtdbus):
                self.assertTrue(retained.exists())

    def test_prunes_dbus_outside_linux(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            qtdbus = self._touch(root, "PySide6/QtDBus.pyd")
            framework_binary = self._touch(
                root, "PySide6/Qt/lib/QtDBus.framework/QtDBus"
            )

            prune_unused_qt_components(root, keep_dbus=False)

            self.assertFalse(qtdbus.exists())
            self.assertFalse(framework_binary.parent.exists())


class TestWindowsPortableShortcut(unittest.TestCase):
    def test_generates_shortcut_for_packaged_executable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir)
            app_dir = build_dir / "bitcap-ipr"
            app_dir.mkdir()
            captured_script = ""

            def capture_command(command: list[str]) -> None:
                nonlocal captured_script
                captured_script = Path(command[2]).read_text(encoding="utf-8")

            with patch(
                "tools.builders.windows.run", side_effect=capture_command
            ) as run_mock:
                shortcut = create_portable_shortcut(
                    PROJECT_METADATA, app_dir, build_dir=build_dir
                )

            command = run_mock.call_args.args[0]
            self.assertEqual(command[0:2], ["cscript.exe", "//nologo"])
            self.assertEqual(command[4], str(app_dir / "BitCapIPR.exe"))
            self.assertEqual(shortcut, build_dir / "BitCapIPR.lnk")
            self.assertIn("shortcut.TargetPath", captured_script)
            self.assertFalse((build_dir / "create-portable-shortcut.js").exists())


class TestResolveReleaseMetadata(unittest.TestCase):
    def test_stable_tag_matches_project_version(self):
        resolved = resolve_release_metadata(
            PROJECT_METADATA, f"v{PROJECT_METADATA.version}"
        )

        self.assertEqual(resolved.version, PROJECT_METADATA.version)

    def test_numbered_preview_tag_embeds_full_version(self):
        preview_version = f"{PROJECT_METADATA.version}-rp2-listen-intent"
        resolved = resolve_release_metadata(PROJECT_METADATA, f"v{preview_version}")

        self.assertEqual(resolved.version, preview_version)
        self.assertEqual(
            resolved.debian_version,
            f"{PROJECT_METADATA.version}~rp.2.listen.intent",
        )

    def test_numbered_preview_tag_allows_omitting_label(self):
        preview_version = f"{PROJECT_METADATA.version}-rp3"
        resolved = resolve_release_metadata(PROJECT_METADATA, f"v{preview_version}")

        self.assertEqual(resolved.version, preview_version)
        self.assertEqual(
            resolved.debian_version,
            f"{PROJECT_METADATA.version}~rp.3",
        )

    def test_legacy_preview_tag_uses_sequence_zero(self):
        preview_version = f"{PROJECT_METADATA.version}-rp-listen-intent"
        resolved = resolve_release_metadata(PROJECT_METADATA, f"v{preview_version}")

        self.assertEqual(resolved.version, preview_version)
        self.assertEqual(
            resolved.debian_version,
            f"{PROJECT_METADATA.version}~rp.0.listen.intent",
        )

    def test_preview_tag_requires_matching_future_version(self):
        future_version = next_patch_version(PROJECT_METADATA.version)
        with self.assertRaisesRegex(
            SystemExit,
            f"expects pyproject.toml version '{future_version}'",
        ):
            resolve_release_metadata(
                PROJECT_METADATA, f"v{future_version}-rp1-listen-intent"
            )

    def test_non_preview_suffix_is_rejected(self):
        with self.assertRaises(SystemExit):
            resolve_release_metadata(
                PROJECT_METADATA,
                f"v{PROJECT_METADATA.version}-beta-listen-intent",
            )


if __name__ == "__main__":
    unittest.main()
