#!/usr/bin/env python

import datetime
import os
import json

from flask import Flask
from flask import request

app = Flask(__name__)
fixtures = '/tmp/fixtures'

def get_ts():
    ts = datetime.datetime.now().isoformat()
    ts = ts.replace('-','_')
    ts = ts.replace(':', '_')
    ts = ts.replace('.', '_')
    return ts


@app.route('/', methods=['GET', 'POST'])
def index():
    print('/')
    print(request.headers)
    print(request.data)

    '''
    ts = datetime.datetime.now().isoformat()
    ts = ts.replace('-','_')
    ts = ts.replace(':', '_')
    ts = ts.replace('.', '_')
    '''
    ts = get_ts()
    logfile = os.path.join(fixtures, 'entries.log')

    if request.data:
        logger_name = 'null_logger'
        host_name = 'null'

        for x in [(request.data, 'data'), (request.headers, 'headers')]:

            isjson = False
            data = x[0]
            if x[1] == 'data':
                data = json.loads(data)
            else:
                data = dict(data)

            if 'logger_name' in data:
                logger_name = data['logger_name']
            if 'host_name' in data:
                host_name = data['host_name']
            dd = os.path.join(fixtures, logger_name)
            if not os.path.isdir(dd):
                os.makedirs(dd)

            df = os.path.join(dd, '%s_%s.%s.json' % (host_name, ts, x[1]))
            with open(df, 'w') as f:
                f.write(json.dumps(data, indent=2, sort_keys=True))
                f.write('\n')

            with open(logfile, 'a') as f:
                f.write('%s %s\n' % (datetime.datetime.now().isoformat(), df))

    return ''

@app.route('/checkpoint/<path:path>', methods=['GET', 'POST'])
def checkpoint(path):
    print(path)
    ts = get_ts()
    logfile = os.path.join(fixtures, 'entries.log')
    with open(logfile, 'a') as f:
        f.write('%s checkpoint %s\n' % (datetime.datetime.now().isoformat(), path))
    return ''

@app.route('/<path:path>', methods=['GET', 'POST'])
def abstract_path(path):
    print(path)
    return ''


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
