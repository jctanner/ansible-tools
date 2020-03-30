#!/usr/bin/env python

import os
import json

import unittest

from ansible_dev_tools.utils import sort_versions


class TestVersionSorting(unittest.TestCase):

    versions = None
    sorted_versions = None

    def setUp(self):
        jfile = 'tests/fixtures/ansible_versions.json'
        with open(jfile, 'r') as f:
            self.versions = json.loads(f.read())
        self.sorted_versions = sort_versions(self.versions)

    def test_devel_is_last(self):
        self.assertEqual(self.sorted_versions[-1], 'devel')

    def test_majors(self):
        expected = [
            self.sorted_versions.index('1.1'),
            self.sorted_versions.index('1.2'),
            self.sorted_versions.index('1.3.0'),
            self.sorted_versions.index('1.4'),
            self.sorted_versions.index('1.5'),
            self.sorted_versions.index('1.6'),
            self.sorted_versions.index('1.7'),
            self.sorted_versions.index('1.8'),
            self.sorted_versions.index('1.9.0.1'),
            self.sorted_versions.index('2.0.0.0'),
            self.sorted_versions.index('2.1.0.0'),
            self.sorted_versions.index('2.2.0.0'),
            self.sorted_versions.index('2.3.0.0'),
            self.sorted_versions.index('2.4.0.0'),
            self.sorted_versions.index('2.5.0'),
            self.sorted_versions.index('2.6.0'),
            self.sorted_versions.index('2.7.0'),
            self.sorted_versions.index('2.8.0'),
            self.sorted_versions.index('2.9.0')
        ]
        actual = sorted(expected)
        self.assertEqual(expected, actual)

    def test_240_sorting(self):
        twothreefour = self.sorted_versions.index('2.3.4.0-0.1.rc1')
        rc1 = self.sorted_versions.index('2.4.0.0-0.1.rc1')
        rc2 = self.sorted_versions.index('2.4.0.0-0.2.rc2')
        rc3 = self.sorted_versions.index('2.4.0.0-0.3.rc3')
        rc4 = self.sorted_versions.index('2.4.0.0-0.4.rc4')
        rc5 = self.sorted_versions.index('2.4.0.0-0.5.rc5')
        final = self.sorted_versions.index('2.4.0.0')

        expected = [twothreefour, rc1, rc2, rc3, rc4, rc5, final]
        actual = sorted(expected)
        self.assertEqual(expected, actual)

    def test_270_sorting(self):
        dev = self.sorted_versions.index('2.7.0.dev0')
        alpha = self.sorted_versions.index('2.7.0a1')
        beta = self.sorted_versions.index('2.7.0b1')
        rc1 = self.sorted_versions.index('2.7.0rc1')
        rc2 = self.sorted_versions.index('2.7.0rc2')
        rc3 = self.sorted_versions.index('2.7.0rc3')
        rc4 = self.sorted_versions.index('2.7.0rc4')
        final = self.sorted_versions.index('2.7.0')

        expected = [dev, alpha, beta, rc1, rc2, rc3, rc4, final]
        actual = sorted(expected)
        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
