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


class TestResolveReleaseMetadata(unittest.TestCase):
    def test_stable_tag_matches_project_version(self):
        resolved = resolve_release_metadata(PROJECT_METADATA, "v1.5.2")

        self.assertEqual(resolved.version, "1.5.2")

    def test_preview_tag_embeds_full_version(self):
        resolved = resolve_release_metadata(PROJECT_METADATA, "v1.5.2-rp-listen-intent")

        self.assertEqual(resolved.version, "1.5.2-rp-listen-intent")
        self.assertEqual(resolved.debian_version, "1.5.2~rp.listen.intent")

    def test_preview_tag_requires_matching_future_version(self):
        with self.assertRaisesRegex(
            SystemExit, "expects pyproject.toml version '1.5.3'"
        ):
            resolve_release_metadata(PROJECT_METADATA, "v1.5.3-rp-listen-intent")

    def test_non_preview_suffix_is_rejected(self):
        with self.assertRaises(SystemExit):
            resolve_release_metadata(PROJECT_METADATA, "v1.5.2-beta-listen-intent")


if __name__ == "__main__":
    unittest.main()
