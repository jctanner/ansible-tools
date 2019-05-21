#!/usr/bin/env python


import argparse
import json

from jinja2 import Environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('template', nargs='+')
    parser.add_argument('--varsfile', nargs='+', help="a json file with vars")
    args = parser.parse_args()

    jvars = {}
    if args.varsfile:
        for vfile in args.varsfile:
            with open(vfile, 'r') as f:
                try:
                    jvars.update(json.loads(f.read()))
                except Exception as e:
                    pass

    jenv = Environment()

    for template in args.template:
        templar = jenv.from_string(template)
        try:
            res = templar.render(**jvars)
        except Exception as e:
            print(e)
            continue
        print(res)
        #import epdb; epdb.st()


if __name__ == "__main__":
    main()
