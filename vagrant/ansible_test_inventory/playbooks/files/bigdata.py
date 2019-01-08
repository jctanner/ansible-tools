#!/usr/bin/python

import json
import os
import random
import sys


def split_args(args):
    newargs = {}
    for kv in args.split():
        parts = kv.split('=', 1)
        try:
            newargs[parts[0]] = parts[1]
        except IndexError:
            pass
    return newargs


def main():

    results = {
        'argv': sys.argv[:],
        'changed': False,
    }

    argfile = sys.argv[1]
    with open(argfile, 'r') as f:
        args = f.read()
    args = split_args(args)
    results['args'] = args

    size = int(args['size'])
    rdata = {}
    chars = ['a','b','c','d','e','f']
    string = ''.join([random.choice(chars) for x in range(0, size)])
    for x in range(0, size):
        rdata['key_%s' % x] = string

    results['data'] = rdata

    print(json.dumps(results))


if __name__ == "__main__":
    main()
