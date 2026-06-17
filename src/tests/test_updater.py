# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest

from mod.updater import (
    is_newer,
    is_prerelease,
    parse_version,
    select_asset,
    version_key,
)


def _asset(name: str) -> dict:
    return {"name": name, "url": f"https://example.com/{name}", "size": 1}


# mirrors the asset names published on a real release.
RELEASE_ASSETS = [
    _asset("BitCapIPR-v1.3.1-macos-15-intel-x64-portable.zip"),
    _asset("BitCapIPR-v1.3.1-macos-15-intel-x64-setup.dmg"),
    _asset("BitCapIPR-v1.3.1-macos-latest-arm64-portable.zip"),
    _asset("BitCapIPR-v1.3.1-macos-latest-arm64-setup.dmg"),
    _asset("BitCapIPR-v1.3.1-ubuntu-22.04-x64-portable.zip"),
    _asset("BitCapIPR-v1.3.1-ubuntu-22.04-x64.deb"),
    _asset("BitCapIPR-v1.3.1-ubuntu-latest-x64-portable.zip"),
    _asset("BitCapIPR-v1.3.1-ubuntu-latest-x64.deb"),
    _asset("BitCapIPR-v1.3.1-win-x64-portable.zip"),
    _asset("BitCapIPR-v1.3.1-win-x64-setup.exe"),
]


class TestParseVersion(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(parse_version("1.3.1"), (1, 3, 1))

    def test_v_prefix(self):
        self.assertEqual(parse_version("v1.3.1"), (1, 3, 1))

    def test_suffix_ignored(self):
        self.assertEqual(parse_version("v2.0.0-beta.1"), (2, 0, 0))

    def test_two_components(self):
        self.assertEqual(parse_version("v2.0"), (2, 0))

    def test_empty(self):
        self.assertEqual(parse_version(""), ())

    def test_no_digits(self):
        self.assertEqual(parse_version("latest"), ())


class TestIsNewer(unittest.TestCase):
    def test_patch_newer(self):
        self.assertTrue(is_newer("v1.3.2", "1.3.1"))

    def test_minor_newer(self):
        self.assertTrue(is_newer("v1.4.0", "1.3.1"))

    def test_major_newer(self):
        self.assertTrue(is_newer("v2.0.0", "1.3.1"))

    def test_equal(self):
        self.assertFalse(is_newer("v1.3.1", "1.3.1"))

    def test_older(self):
        self.assertFalse(is_newer("v1.3.0", "1.3.1"))

    def test_uneven_length_newer(self):
        self.assertTrue(is_newer("v1.3.1", "1.3"))

    def test_uneven_length_equal(self):
        self.assertFalse(is_newer("v1.3.0", "1.3"))

    def test_unparseable_latest(self):
        self.assertFalse(is_newer("", "1.3.1"))

    def test_prerelease_preview_of_higher_version(self):
        # a preview of an upcoming patch is newer than the current release.
        self.assertTrue(is_newer("v1.4.2-rp-hivegpu", "1.4.1"))

    def test_final_release_supersedes_its_prerelease(self):
        self.assertTrue(is_newer("v1.4.2", "1.4.2-rp-hivegpu"))

    def test_prerelease_not_newer_than_final(self):
        # a preview of the version you already run is not an upgrade.
        self.assertFalse(is_newer("v1.4.2-rp-hivegpu", "1.4.2"))

    def test_sibling_prereleases_not_comparable(self):
        # two feature previews of the same base never supersede each other.
        self.assertFalse(is_newer("v1.4.2-rp-hivegpu", "1.4.2-rp-pools"))
        self.assertFalse(is_newer("v1.4.2-rp-pools", "1.4.2-rp-hivegpu"))

    def test_equal_prerelease(self):
        self.assertFalse(is_newer("v1.4.2-rp-hivegpu", "1.4.2-rp-hivegpu"))


class TestIsPrerelease(unittest.TestCase):
    def test_prerelease_tag(self):
        self.assertTrue(is_prerelease("v1.4.2-rp-hivegpu"))

    def test_final_tag(self):
        self.assertFalse(is_prerelease("v1.4.2"))

    def test_empty(self):
        self.assertFalse(is_prerelease(""))


class TestVersionKey(unittest.TestCase):
    def test_prerelease_orders_before_final(self):
        self.assertLess(version_key("v1.4.2-rp-hivegpu"), version_key("v1.4.2"))

    def test_sibling_prereleases_share_a_key(self):
        self.assertEqual(
            version_key("v1.4.2-rp-hivegpu"), version_key("v1.4.2-rp-pools")
        )

    def test_higher_base_wins_over_prerelease(self):
        self.assertGreater(version_key("v1.4.2-rp-hivegpu"), version_key("v1.4.1"))

    def test_max_prefers_prerelease_of_highest_base(self):
        # newest-first order; max keeps the first of a tie (most recent).
        tags = ["v1.4.2-rp-pools", "v1.4.2-rp-hivegpu", "v1.4.1", "v1.3.2"]
        self.assertEqual(max(tags, key=version_key), "v1.4.2-rp-pools")


class TestSelectAsset(unittest.TestCase):
    def test_windows_picks_setup_exe(self):
        asset = select_asset(RELEASE_ASSETS, "windows", False)
        self.assertEqual(asset["name"], "BitCapIPR-v1.3.1-win-x64-setup.exe")

    def test_windows_portable_when_not_prefer_installer(self):
        asset = select_asset(RELEASE_ASSETS, "windows", False, prefer_installer=False)
        self.assertEqual(asset["name"], "BitCapIPR-v1.3.1-win-x64-portable.zip")

    def test_windows_arm_has_no_match(self):
        self.assertIsNone(select_asset(RELEASE_ASSETS, "windows", True))

    def test_macos_intel_picks_intel_dmg(self):
        asset = select_asset(RELEASE_ASSETS, "macos", False)
        self.assertEqual(asset["name"], "BitCapIPR-v1.3.1-macos-15-intel-x64-setup.dmg")

    def test_macos_arm_picks_arm_dmg(self):
        asset = select_asset(RELEASE_ASSETS, "macos", True)
        self.assertEqual(asset["name"], "BitCapIPR-v1.3.1-macos-latest-arm64-setup.dmg")

    def test_linux_picks_a_deb(self):
        asset = select_asset(RELEASE_ASSETS, "linux", False)
        self.assertTrue(asset["name"].endswith(".deb"))

    def test_linux_selection_is_deterministic(self):
        first = select_asset(RELEASE_ASSETS, "linux", False)
        second = select_asset(list(reversed(RELEASE_ASSETS)), "linux", False)
        self.assertEqual(first["name"], second["name"])

    def test_no_assets(self):
        self.assertIsNone(select_asset([], "linux", False))

    def test_unrelated_assets(self):
        assets = [_asset("BitCapIPR-v1.3.1-source.tar.gz")]
        self.assertIsNone(select_asset(assets, "windows", False))


if __name__ == "__main__":
    unittest.main()
