# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import unittest

from mod.updater import is_newer, parse_version


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


if __name__ == "__main__":
    unittest.main()
