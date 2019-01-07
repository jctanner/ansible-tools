#!/usr/bin/python


import json
import os
import sys

from sh import vagrant


def split_args(args):
    newargs = {}
    for kv in args.split():
        parts = kv.split('=', 1)
        try:
            newargs[parts[0]] = parts[1]
        except IndexError:
            pass
    return newargs


def split_ssh_config(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    ssh_config = {}
    for line in raw.split('\n'):    
        line = line.strip()
        parts = line.split(None, 1)
        try:
            ssh_config[parts[0]] = parts[1].strip()
        except IndexError:
            pass
    return ssh_config


def main():
    
    results = {
        'argv': sys.argv[:],
        'changed': False,
        'stdin': sys.stdin.read(),
        #'env': dict(os.environ)
    }

    argfile = sys.argv[1]
    with open(argfile, 'r') as f:
        args = f.read()
    args = split_args(args)
    results['args'] = args

    assert 'boxpath' in args, 'args must contain a boxpath'

    boxpath = args['boxpath']
    boxpath = boxpath.replace("'", "")
    boxpath = boxpath.replace('"', "")
    boxpath = os.path.expanduser(boxpath)
    boxpath = os.path.abspath(boxpath)
    pid = vagrant('ssh-config', _cwd=boxpath)
    pid.wait()
    results['ssh_config'] = split_ssh_config(pid.stdout)

    print(json.dumps(results))    


if __name__ == "__main__":
    main()
