#!/usr/bin/env python

import argparse
import functools
import glob
import json
import os
import re
import shutil
import subprocess
import sys

from collections import OrderedDict

from pprint import pprint

import requests
from bs4 import BeautifulSoup
from sh import curl
from sh import git
from sh import tar
from logzero import logger

from distutils.version import LooseVersion
from packaging.version import Version

from ansible_tools.config import ANSIBLE_TOOLS_CACHEDIR



def run_command(args, env=None, capture=False, shell=True):
    kwargs = {'shell': True}
    if capture:
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
    if env:
        kwargs['env'] = env
    p = subprocess.Popen(args, **kwargs)

    (so, se) = p.communicate()
    return (p.returncode, so, se)


class Version2(Version):

    @property
    def version(self):
		# (Epdb) pp vmap['v2.4.0.0-0.4.rc4'].version
		# [2, 4, 0, 0, '-', 0, 4, 'rc', 4]
        version = self.base_version
        return version


def vcompare(version):
    #[2, 8, 0, 'a', 1]
    #[2, 8, 0, 'b', 1]
    #[2, 8, 0, 'rc', 1]
    #[2, 8, 0, 'rc', 2]
    #[2, 8, 0, 'rc', 3]
    #[2, 8, 0]

    print(version)

    version = version.version
    if not isinstance(version, list):
        version = version.split('.')
    while [x for x in version if not isinstance(x, int)]:
        for ix,x in enumerate(version):
            if isinstance(x, int):
                continue
            if x == 'rc' or x.endswith('rc'):
                version[ix] = -1
            elif x == 'b' or x.endswith('b'):
                version[ix] = -2
            elif x == 'beta' or x.endswith('beta'):
                version[ix] = -2
            elif x == 'a' or x.endswith('a'):
                version[ix] = -3
            elif x == 'dev' or x.endswith('dev'):
                version[ix] = -4
            elif not isinstance(x, int):
                del version[ix]

    '''
    if len(version) < 2:
        import epdb; epdb.st()

    if version[0] == 2 and version[1] == 5:
        import epdb; epdb.st()

    while len(version) < 8:
        version.append(0)
    '''

    #version = [999 + x for x in version]
    total = 0
    print(version)
    enumerated= []
    for idx,x in enumerate(version):
        '''
        if idx == -1:
            total += (float(8) / idx) * (1 + x)
        elif x < 0:
            total += (float(8) / idx) * (1 + x)
        else:
            total += (float(8) / idx + 1) * (1 + x)
        '''

        '''
        idx += 1
        #nt = (float(8) / idx) * x
        if x == 0:
            nt = (float(8 - idx)) / (x+1)
        else:
            nt = (float(8 - idx) / (x+1))
        print('\t%s:%s == %s' % (idx, x, nt))
        total += nt
        '''

        '''
        base = [9] * (2 * (len(version) - idx))
        print('\t%s' % base)
        basesum = sum(base)
        print('\t%s:%s basesum:%s' % (idx, x, basesum))
        ns = (basesum + x)
        print('\t%s:%s == %s' % (idx, x, ns))
        total += ns
        #import epdb; epdb.st()
        '''

        '''
        base = [9] * (2 * (len(version) - idx))
        print('\t%s' % base)
        basesum = sum(base)
        print('\t%s:%s basesum:%s' % (idx, x, basesum))
        ns = total * (basesum + x)
        print('\t%s:%s == %s' % (idx, x, ns))
        total += ns
        #import epdb; epdb.st()
        '''
        base = [9] * 1000 * (len(version) - idx)
        if x == 0:
            #ns = sum(base) + x
            #ns = sum(base) / x
            ns = sum(base)
        #elif x == 0:
        #    ns = sum(base)
        else:
            #ns = sum(base) - (-2 * x)
            #ns = sum(base) / x
            ns = sum(base) / x
        enumerated.append(ns)
        #import epdb; epdb.st()
        total += ns


    print('TOTAL %s=%s %s' % (version,total, enumerated))
    #return total
    return enumerated
    #import epdb; epdb.st()

    #import epdb; epdb.st()
    #print(version)
    #return version



def _version_to_list(version):
    separator_words = [
        ['rc'],
        ['beta', 'b'],
        ['alpha', 'a'],
        ['dev']
    ]

    # 1.9.6-0.1.rc1
    if '-' in version:
        parts = version.split('-')
        subver = parts[-1].split('.')[-1]
        if len(parts[0].split('.')) == 3:
            parts[0] += '.0'
        _version = parts[0] + subver
    else:
        _version = version

    _version = _version.split('.')
    for idx,x in enumerate(_version):
        try:
            _version[idx] = float(x)
        except Exception as e:
            print(e)
            nx = x
            thissep = None
            for ids,separators in enumerate(separator_words):

                for sep in separators:
                    if sep in x:
                        thissep = sep
                        break

                if thissep is not None:
                    break

            if thissep == 'dev':
                _version[idx-1] -= 10

            #if thissep is None:
            #    import epdb; epdb.st()

            nx = x.replace(thissep, '.' + '0' * ids)
            #import epdb; epdb.st()

            #print('%s == %s' % (x, nx))
            #import epdb; epdb.st()

            #_version[idx] = 0 - float(nx)
            _version[idx] = (0 + float(nx)) - idx
            '''
            try:
                _version[idx] = 0 - float(nx)
            except ValueError as e:
                print(e)
                import epdb; epdb.st()
            '''

    return _version

def sort_versions(versions):

    devel = False
    if 'devel' in versions:
        devel = True
        versions.remove('devel')

    # make each version a numerical list for sorting
    _versions = [_version_to_list(x) for x in versions]

    # make the same number of bits
    vmax = max([len(x) for x in _versions])
    for idv,_version in enumerate(_versions):
        while len(_versions[idv]) < vmax:
            _versions[idv].append(0.0)

    # map orig to new list
    vmap = dict(zip(versions, _versions))

    # sort by the lists
    vsorted = sorted(vmap.items(), key=lambda x: x[1])

    # return original string
    result = [x[0] for x in vsorted]

    if devel:
        result.append('devel')

    return result


def _sort_versions(versions):

    '''
    vfile = '/tmp/versions.json'
    if not os.path.exists(vfile):
        with open(vfile, 'w') as f:
            f.write(json.dumps(versions))
    '''

    vmap = dict(zip(versions[:], versions[:]))
    devel = None
    usev = False

    for k,v in vmap.items():
        if v.startswith('devel'):
            devel = k
            continue
        if v.startswith('v'):
            usev = True
            v = v[1:]

        # Try Version or LooseVersion where possible
        for x in ['Version', 'LooseVersion']:
            try:
                if x == 'Version' and v.startswith('2.5'):
                    v = Version2(v)
                    converted = True
                    break
                elif x == 'LooseVersion':
                    v = LooseVersion(v)
                    converted = True
                    break
            except Exception as e:
                pass

        vmap[k] = vcompare(v)
        vmap[k] = v

    # save devel for last
    if devel:
        vmap.pop(devel, None)

    # sort by version
    #_versions = sorted(vmap.items(), key=lambda tup: str(tup[1]))
    #_versions = sorted(vmap.items(), key=lambda tup: tup[1])
    x1_versions = sorted([x for x in vmap.items() if x[1].version[0] == 1], key=lambda tup: tup[1])
    x2_versions = sorted([x for x in vmap.items() if x[1].version[0] == 2], key=lambda tup: tup[1])
    #_versions = sorted(vmap.items(), key=lambda tup: tup[1])
    import epdb; epdb.st()

    # get the original keys
    final_sorted_versions = [x[0] for x in _versions] + [devel]

    #for fv in final_sorted_versions:
    #    print(fv)

    from pprint import pprint; pprint(final_sorted_versions)
    import epdb; epdb.st()
    return final_sorted_versions


class AnsibleVersionTester(object):
    DEVEL_URL = 'https://github.com/ansible/ansible'
    RELEASES_URL = "https://releases.ansible.com/ansible"
    ENV_SETUP = 'https://raw.githubusercontent.com/ansible/ansible/devel/hacking/env-setup'

    def __init__(self, cachedir=None):
        if cachedir is None:
            cachedir = ANSIBLE_TOOLS_CACHEDIR
        self.cachedir = cachedir
        self.extractdir = os.path.join(self.cachedir, 'extracted')
        self.develdir = os.path.join(self.cachedir, 'checkouts', 'ansible-devel')
        self.build_cache_dirs()
        self.download_versions()
        self.extract_versions()
        self.create_hacking()
        self.update_devel()

    def list_versions(self):
        versions = self.versions
        versions = [x.replace('ansible-', '') for x in versions]
        versions = sort_versions(versions)
        for version in versions:
            print(version)

    @property
    def versions(self):
        rr = requests.get(self.RELEASES_URL)
        soup = BeautifulSoup(rr.text, features='html.parser')
        hrefs = soup.findAll('a')
        hrefs = [x.attrs['href'] for x in hrefs]
        hrefs = [x for x in hrefs if x.endswith('.gz')]
        hrefs = [x for x in hrefs if 'latest' not in x]
        hrefs = [x.replace('.tar.gz', '') for x in hrefs]
        hrefs.append('ansible-devel')
        return hrefs

    def build_cache_dirs(self):
        cachedirs = [
            self.cachedir,
            os.path.join(self.cachedir, 'tars'),
            os.path.join(self.cachedir, 'extracted')
        ]
        for cachedir in cachedirs:
            if not os.path.exists(cachedir):
                try:
                    os.makedirs(cachedir)
                except PermissionError as e:
                    logger.error('You must manually create the path "%s"' % cachedir)
                    sys.exit(1)

    def update_devel(self):
        if not os.path.exists(self.develdir):
            logger.debug('git clone %s %s' % (self.DEVEL_URL, self.develdir))
            git('clone', self.DEVEL_URL, self.develdir)
        else:
            cmd = 'cd %s; git fetch -a; git pull --rebase origin devel' % self.develdir
            logger.debug(cmd)
            run_command(cmd)

    def download_versions(self, version=None):
        rr = requests.get(self.RELEASES_URL)
        soup = BeautifulSoup(rr.text, features='html.parser')
        hrefs = soup.findAll('a')
        hrefs = [x.attrs['href'] for x in hrefs]
        hrefs = [x for x in hrefs if x.endswith('.gz')]
        hrefs = [x for x in hrefs if 'latest' not in x]

        # filter by specific version if requested
        if version:
            hrefs = [x for x in hrefs if version in x]

        for href in hrefs:
            dst = os.path.join(self.cachedir, 'tars', href)
            src = os.path.join(self.RELEASES_URL, href)
            if not os.path.exists(dst):
                logger.debug('%s -> %s' % (dst,src))
                res = curl('-o', dst, src)
                if res.exit_code != 0:
                    logger.error('Failed to download %s to %s' % (src, dst))
                    logger.error(res.stdout)
                    logger.error(res.stderr)
                    sys.exit(1)

    def extract_versions(self, version=None):
        tarballs = glob.glob('%s/tars/*.gz' % self.cachedir)
        if version:
            tarballs = [x for x in tarballs if version in x]
        for tarball in tarballs:
            dst = os.path.join(
                self.extractdir,
                os.path.basename(tarball).replace('.tar.gz', '')
            )
            if not os.path.exists(dst):
                # extract to temp dir first to avoid clobbering
                temp_dst = dst + '.tmp'
                if os.path.exists(temp_dst):
                    shutil.rmtree(temp_dst)
                os.makedirs(temp_dst)
                logger.debug('tar xzf %s -C %s' % (tarball, temp_dst))
                try:
                    res = tar('xzf', tarball, '-C', temp_dst)
                except Exception as e:
                    logger.error(e)
                    sys.exit(1)
                # what was the extracted root path?
                edirs = glob.glob('%s/*' % temp_dst)
                srcdir = edirs[0]

                # move the extract to the right place
                shutil.move(srcdir, dst)
                shutil.rmtree(temp_dst)

    def create_hacking(self, version=None):
        extracts = glob.glob('%s/*' % self.extractdir)
        for extract in extracts:
            dst = os.path.join(extract, 'hacking')
            if not os.path.exists(dst):
                os.makedirs(dst)
                env_dst = os.path.join(dst, 'env-setup')
                logger.debug(env_dst)
                res = curl('-o', env_dst, self.ENV_SETUP)

    def test_version(self, python, version, params):
        '''Run a test script through hacking'''
        vdir = os.path.join(self.extractdir, version)
        if not os.path.exists(vdir):
            if version == 'ansible-devel':
                vdir = self.develdir
            else:
                raise Exception('%s does not exist')
        hacking_script = os.path.join(vdir, 'hacking', 'env-setup')
        command = 'source %s >/dev/null 2>&1 ; %s' % (hacking_script, params)

        if 'ansible-playbook' in command:
            command = command.replace('ansible-playbook', os.path.join(vdir, 'bin', 'ansible-playbook'))
        if 'ansible-doc' in command:
            command = command.replace('ansible-doc', os.path.join(vdir, 'bin', 'ansible-doc'))
        if 'ansible ' in command:
            command = command.replace('ansible ', os.path.join(vdir, 'bin', 'ansible') + ' ')

        env = os.environ.copy()
        env['ANSIBLE_TEST_VERSION'] = version
        if python:
            env['TEST_PYTHON'] = python
        logger.info(command)
        (rc, so, se) = run_command(command, capture=False, env=env)
        print(so)
        print(se)
        return rc

    def run_test(self, start=None, version=None, python=None, command=None):

        ansible_versions = self.versions[:]

        if start:
            av_tmp = []
            keep = False
            for av in ansible_versions:
                if av.startswith('v' + str(start)):
                    keep = True
                elif av.startswith('ansible-%s' % start):
                    keep = True
                if keep:
                    av_tmp.append(av)
            ansible_versions = [x for x in av_tmp]

        if version:
            ansible_versions = \
                    [x for x in ansible_versions if x == 'ansible-%s' % version]

        # use a script if given, otherwise it's a command
        if os.path.isfile(command):
            if not os.access(command, os.X_OK):
                os.chmod(command, 0o700)
            command = './%s' % command
        else:
            if python:
                command = '%s %s' % (python, command)
            else:
                command = 'bash %s' % command

        LOGFILE = 'ansible_versions.log'
        if os.path.isfile(LOGFILE):
            os.remove(LOGFILE)

        results = []
        for x in ansible_versions:
            logger.info('###################################')
            logger.info("# TESTING: %s" % x)
            logger.info('###################################')
            rc = self.test_version(python, x, command)
            results.append((x, rc))
            with open(LOGFILE, 'a') as f:
                f.write('%s ; %s\n' % (x, rc))

        logger.info('###################################')
        logger.info('#            RESULTS              #')
        logger.info('###################################')
        pprint(results)

