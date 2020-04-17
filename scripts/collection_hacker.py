#!/usr/bin/env python

import json
import os

import yaml
import ansible

from ansible.plugins.loader import get_all_plugin_loaders


class CollectionChecker:

    _ERRORS = None    
    _collections = None
    _loaders = None

    def __init__(self):

        self._ERRORS = []
        self._collections = self.find_all_collections()
        loaders = get_all_plugin_loaders()
        self._loaders = dict(loaders)

        results = {}
        for cfp,cd in self._collections.items():

            for ptype,pfiles in cd['plugins'].items():

                # doc fragments aren't real plugins yet?
                if ptype == 'doc_fragments':
                    continue

                lkeys = [
                    ptype + '_loader',
                    ptype + 's_loader',
                ]
                thisloader = None
                for lkey in lkeys:
                    if lkey in self._loaders:
                        thisloader = self._loaders[lkey]
                        break
                if not thisloader:
                    continue

                for pfile in pfiles:
                    if os.path.basename(pfile) == '__init__.py':
                        continue
                    sp1 = os.path.splitext(pfile)[0]
                    sp1 = sp1.replace('/', '.')
                    if cd['fqcn']:
                        sp2 = cd['fqcn'] + '.' + sp1
                    else:
                        sp2 = None
                    for cp in [sp1, sp2]:
                        if cp is None:
                            continue
                        try:
                            results[(cfp, ptype, pfile, cp)] = thisloader.find_plugin(cp)
                        except ansible.errors.AnsibleError:
                            pass

        for item in results.items():
            self.check_result(*item)

        print('%s plugin finding errors found' % len(self._ERRORS))
        codes = [x.split(':', 1)[0] for x in self._ERRORS]
        _codes = sorted(set(codes))
        for _code in _codes:
            print('\_%s %s codes' % (len([x for x in codes if x == _code]), _code))

    def check_result(self, key, result):
        if result is not None:
            return

        eprefix = '[%s][%s] "%s" failed because' % (
            key[0],
            key[1],
            key[3],
        )
        if 'ansible_collections' not in key[0]:
            self._ERRORS.append('ERRPL1: %s "%s" does not have "ansible_collections" in it\'s path' % (
                eprefix,
                key[0]
            ))
        if '.' not in key[-1]:
            self._ERRORS.append('ERRPL2: %s "%s" is not an fqcn or this plugin is not setup in routing.yml' % (eprefix, key[-1]))


    def find_all_collections(self):
        collections = {}
        locations = [
            './ansible_collections',
            './collections',
            '~/.ansible/collections',
            '~/.ansible/ansible_collections',
            '~/.ansible',
            '.'
        ]
        for location in locations:
            ep = os.path.expanduser(location)

            for dirName, subdirList, fileList in os.walk(ep, followlinks=True):

                if 'tests/integration' in dirName:
                    continue
                if 'tests/unit' in dirName:
                    continue
                
                if 'plugins' in subdirList or 'roles' in subdirList:

                    if 'ansible_collections' not in dirName:
                        self._ERRORS.append('ENOACDIR: %s' % dirName)
                        print(self._ERRORS[-1])

                    collections[dirName] = {}

        for fp,v in collections.items():
            v = {
                'meta': None,
                'namespace': None,
                'name': None,
                'fqcn': None,
                'plugins': {},
                'roles': {}
            }

            has_meta = False
            for fn in ['galaxy.yml', 'MANIFEST.json']:
                fn = os.path.join(fp, fn)
                if os.path.exists(fn):
                    has_meta = True
                    if fn.endswith('.yml') or fn.endswith('.yaml'):
                        with open(fn, 'r') as f:
                            v['meta'] = yaml.load(f.read())
                    elif fn.endswith('.json'):
                        with open(fn, 'r') as f:
                            v['meta'] = json.loads(f.read())
                    v['namespace'] = v['meta']['collection_info']['namespace']
                    v['name'] = v['meta']['collection_info']['name']
                    v['fqcn'] = v['meta']['collection_info']['namespace'] + '.' + v['meta']['collection_info']['name']
                    break

            if not has_meta:
                self._ERRORS.append('ENOMETA: %s' % fp)
            if v['fqcn'] is None:
                self._ERRORS.append('ENOFQCN: %s'% fp)

            for dirName, subdirList, fileList in os.walk(os.path.join(fp, 'plugins'), followlinks=True):
                #print(dirName)
                paths = dirName.split('/')
                #print(paths)
                pindex = paths.index('plugins')
                try:
                    ptype = paths[pindex+1]
                except IndexError:
                    continue
                
                if ptype not in v['plugins']:
                    v['plugins'][ptype] = []

                prefix = os.path.join(*paths[:pindex+2])
                if dirName.endswith(prefix):
                    dn = dirName.replace(prefix, '')
                else:
                    dn = dirName.replace(prefix + '/', '')
                if dn == '/':
                    dn = ''
                #import epdb; epdb.st()

                for fn in fileList:
                    if dn == '/':
                        import epdb; epdb.st()
                    fn = os.path.join(dn, fn)
                    if fn.startswith('/'):
                        fn = fn[1:]
                    v['plugins'][ptype].append(fn)

            collections[fp] = v
            
        return collections


def main():
    CollectionChecker()


if __name__ == "__main__":
    main()
