#!/usr/bin/env python

import os
import json

import unittest

from ansible_tools.utils import sort_versions

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


if __name__ == '__main__':
    unittest.main()



