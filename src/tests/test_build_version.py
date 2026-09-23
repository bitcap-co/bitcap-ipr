# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_DIR), str(ROOT_DIR / "tools")]

from tools.build_app import resolve_release_metadata
from tools.project_metadata import load_metadata

PROJECT_METADATA = load_metadata()


def next_patch_version(version: str) -> str:
    major, minor, patch = map(int, version.split("."))
    return f"{major}.{minor}.{patch + 1}"


class TestResolveReleaseMetadata(unittest.TestCase):
    def test_stable_tag_matches_project_version(self):
        resolved = resolve_release_metadata(
            PROJECT_METADATA, f"v{PROJECT_METADATA.version}"
        )

        self.assertEqual(resolved.version, PROJECT_METADATA.version)

    def test_preview_tag_embeds_full_version(self):
        preview_version = f"{PROJECT_METADATA.version}-rp-listen-intent"
        resolved = resolve_release_metadata(PROJECT_METADATA, f"v{preview_version}")

        self.assertEqual(resolved.version, preview_version)
        self.assertEqual(
            resolved.debian_version,
            f"{PROJECT_METADATA.version}~rp.listen.intent",
        )

    def test_preview_tag_requires_matching_future_version(self):
        future_version = next_patch_version(PROJECT_METADATA.version)
        with self.assertRaisesRegex(
            SystemExit,
            f"expects pyproject.toml version '{future_version}'",
        ):
            resolve_release_metadata(
                PROJECT_METADATA, f"v{future_version}-rp-listen-intent"
            )

    def test_non_preview_suffix_is_rejected(self):
        with self.assertRaises(SystemExit):
            resolve_release_metadata(
                PROJECT_METADATA,
                f"v{PROJECT_METADATA.version}-beta-listen-intent",
            )


if __name__ == "__main__":
    unittest.main()
