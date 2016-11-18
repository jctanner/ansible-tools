#!/usr/bin/env python

import importlib
import imp
import glob
import os
import random
import shutil
import sys
import tempfile
import uuid
import unittest
from pprint import pprint


# THIS IS A HACK TO IMPORT FROM THE SCRIPTS
LIBDIR = tempfile.mkdtemp()
LIBDIR = os.path.join(LIBDIR, 'lib')
if not os.path.isdir(LIBDIR):
    os.makedirs(LIBDIR)
with open(os.path.join(LIBDIR, '__init__.py'), 'wb') as f:
    f.write('')
libfiles = glob.glob('*')
libfiles = [x for x in libfiles if '-' in x and not x.endswith('.py')]
#pprint(libfiles)
for lf in libfiles:
    dst = os.path.join(LIBDIR, '%s.py' % lf.replace('-', ''))
    shutil.copy(lf, dst)
sys.path.insert(0, LIBDIR)

from ansiblebisect import AnsibleBisector

# hash,rc,so,se,version,date
TESTCOMMITS = [
    ('aaa', 0, '', '', '1.0', '2016-01-01T00:00:00'),
    ('aab', 0, '', '', '1.0', '2016-01-02T00:00:00'),
    ('aac', 0, '', '', '1.0', '2016-01-03T00:00:00'),
    ('aad', 0, '', '', '1.0', '2016-01-04T00:00:00'),
    ('aae', 1, '', '', '1.0', '2016-01-05T00:00:00'),
    ('aaf', 1, '', '', '1.0', '2016-01-06T00:00:00'),
    ('aag', 1, '', '', '1.0', '2016-01-07T00:00:00'),
]


class TestAnsibleBisector(unittest.TestCase):
    def get_commit(self, commit, commits):
        index = None
        for idx,x in enumerate(commits):
            if x[0] == commit:
                index = idx
                break
        return commits[index]

    def test_basic(self):
        print('')
        ab = AnsibleBisector([x[0] for x in TESTCOMMITS])

        # get the first test
        tc = ab.get_commit_to_test()
        while tc:
            ctuple = self.get_commit(tc, TESTCOMMITS)
            ab.set_result(tc, ctuple[1], ctuple[2], ctuple[3])
            tc = ab.get_commit_to_test()

        bad_commit = ab.get_bisected_commit()
        assert bad_commit == 'aae', "bisected wrong commit"

    def test_random_iterations(self):
        print('')

        for i in xrange(0, 1000):

            # make a randomly sized list of commits
            total = random.randrange(0, 20000)
            testcommits = [[str(uuid.uuid4()), 0] for x in xrange(0,total)]

            # set a random marker
            marker = random.randrange(0, len(testcommits))
            bad_commit = testcommits[marker][0]

            # change the rc for all commits starting at the marker
            for idx,x in enumerate(testcommits):
                if idx >= marker:
                    testcommits[idx][1] = 1

            ab = AnsibleBisector([x[0] for x in testcommits])

            # get the first test
            tc = ab.get_commit_to_test()
            while tc:
                ctuple = self.get_commit(tc, testcommits)
                ab.set_result(tc, ctuple[1], '', '')
                tc = ab.get_commit_to_test()

            bisected_commit = ab.get_bisected_commit()
            print("EXPECTED: %s" % bad_commit)
            print("BISECTED: %s" % bisected_commit)
            assert bisected_commit == bad_commit, "bisected wrong commit"

