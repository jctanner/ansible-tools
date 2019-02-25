#!/usr/bin/env python

import json
import os
import statistics
import sys

from collections import OrderedDict

def main():
    rd = sys.argv[1]
    obsfile = os.path.join(rd, '.cache', 'observations.json')
    assert os.path.exists(obsfile)

    with open(obsfile, 'r') as f:
        rows = json.loads(f.read())
    #rows = sorted(rows, key=lambda x: x['ts'])

    t0 = rows[0]['ts']
    tN = rows[-1]['ts']

    tasks = OrderedDict()
    current_task = None
    for ird,row in enumerate(rows):
        if row.get('task_name'):
            current_task = row['task_name']
            if current_task not in tasks:
                tasks[current_task] = {
                    't0': row['ts'],
                    'tN': row['ts'],
                    'hosts': {}
                }
            tasks[current_task]['tN'] = row['ts']

            if row.get('host'):
                hn = row['host']
                if hn not in tasks[current_task]['hosts']:
                    tasks[current_task]['hosts'][hn] = {
                        't0': row['ts'],
                    }
                tasks[current_task]['hosts'][hn]['tN'] = row['ts']

    fastest_task = None
    slowest_task = None
    for k,v in tasks.items():
            tasks[k]['tD'] = v['tN'] - v['t0']
            if not slowest_task or tasks[slowest_task]['tD'] < tasks[k]['tD']:
                slowest_task = k 
            if not fastest_task or tasks[fastest_task]['tD'] > tasks[k]['tD']:
                fastest_task = k 

            for hn,hv in v['hosts'].items():
                tasks[k]['hosts'][hn]['tD'] = hv['tN'] - hv['t0']

    hNdeltas = []
    bottlenecks = []
    most_variance = None
    for k,v in tasks.items():
        durations = []

        hds = []
        for hn,hv in v['hosts'].items():
            durations.append(hv['tD'])
            hds.append([hn, hv['t0'], hv['tN']])

        tasks[k]['host_mean'] = statistics.mean(durations)
        tasks[k]['host_pvariance'] = statistics.pvariance(durations)
        if not most_variance or tasks[k]['host_pvariance'] > tasks[most_variance]['host_pvariance']:
            most_variance = k

        std = statistics.pstdev(durations)
        for hn,hv in v['hosts'].items():
            md = hv['tD'] - tasks[k]['host_mean']
            if md > (std):
                bottlenecks.append([k, hn, hv['tD'], tasks[k]['host_mean'], std, md / std])
        hds = sorted(hds, key=lambda x: x[-1])
        hNdelta = hds[-1][-1] - hds[-2][-1]
        if hNdelta > (tasks[k]['host_mean'] + std):
            hNdeltas.append([k, hds[-1][0], hNdelta])
            #import epdb; epdb.st()

    hNdelta_wait_total = sum([x[-1] for x in hNdeltas])
    hNdelta_wait_percent = hNdelta_wait_total / (tN-t0)

    print('total duration: %ss' % (tN - t0))
    print('fastest task: (%ss) %s'  % (tasks[fastest_task]['tD'], fastest_task))
    print('slowest task: (%ss) %s'  % (tasks[slowest_task]['tD'], slowest_task))
    print('task with most host duration variance: (%s) %s' % (tasks[most_variance]['host_pvariance'], most_variance))
    print('[%s] %ss of %ss was spent waiting on the slowest host(s) in the batch' % (hNdelta_wait_percent, hNdelta_wait_total, (tN-t0)))
    
    #import epdb; epdb.st()


if __name__ == "__main__":
    main()
