#!/usr/bin/env python

import datetime
import json
import os
import sys
import time

import pytz
import svgwrite

from svgwrite import cm, mm, percent
from svgwrite import percent as pc
from logzero import logger


def get_observations_from_delphiki():
    #fn = 'jobresults.2.7.7/.cache/observations.json'
    #fn = 'rhtestOct17/270/.cache/observations.json'
    #fn = 'rhtestOct17/242/.cache/observations.json'

    #fn = 'rhtest-02-14-2019/jobresults.2.4.6.0/.cache/observations.json'
    #fn = 'rhtest-02-14-2019/jobresults.2.8.0.dev0/.cache/observations.json'

    dn = sys.argv[1]
    fn = os.path.join(dn, '.cache', 'observations.json')
    if not os.path.exists(fn):
        raise Exception('%s does not exist' % fn)
    logger.info('reading %s' % fn)
    with open(fn, 'r') as f:
        obs = json.loads(f.read())
    logger.info('%s observations found' % len(obs))
    return obs


def get_observations_from_baseline():
    dn = sys.argv[1]
    fn = os.path.join(dn, 'baseline.json')
    if not os.path.exists(fn):
        raise Exception('%s does not exist' % fn)
    logger.info('reading %s' % fn)
    with open(fn, 'r') as f:
        baseline = json.loads(f.read())

    # adapt the baseline dict to events
    observations = []
    obs = {
        'host': None,
        'ts': baseline[0]['play']['duration']['start'],
        'task_name': None,
        #'fn': fn
    }
    observations.append(obs)
    for task in baseline[0]['tasks']:
        tn = task['task']['name']
        for hn,hd in task['hosts'].items():
            for key in ['start', 'end']:
                obs = {
                    'task_name': tn,
                    'host': hn,
                    'ts': hd['duration'][key],
                    #'fn': fn
                }
                observations.append(obs)
            #import epdb; epdb.st()
    obs = {
        'host': None,
        'ts': baseline[0]['play']['duration']['end'],
        'task_name': None,
        #'fn': fn
    }
    observations.append(obs)

    for idx,x in enumerate(observations):
        ts = x['ts']
        # 2019-02-22T02:22:21.249551
        ts = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f')
        #ts = time.mktime(ts.timetuple())
        ts = ts.timestamp()
        observations[idx]['ts'] = ts
    observations = sorted(observations, key=lambda x: x['ts'])
    #import epdb; epdb.st()
    return observations


def get_vmstats():
    dn = sys.argv[1]
    fn = os.path.join(dn, 'vmstat.log')
    if not os.path.exists(fn):
        raise Exception('%s does not exist' % fn)
    logger.info('reading %s' % fn)
    with open(fn, 'r') as f:
        lines = f.readlines() 

    rows = []
    VMSTAT_TIMEZONE = None
    for line in lines:
        cols = line.split()
        if cols[0] == 'procs':
            continue
        if cols[0] == 'r':
            VMSTAT_TIMEZONE = cols[-1]
            continue

        data = {
            'vmstat_r': int(cols[0]),
            'vmstat_b': int(cols[1]),
            'vmstat_swpd': int(cols[2]),
            'vmstat_free': int(cols[3]),
            'vmstat_buff': int(cols[4]),
            'vmstat_cache': int(cols[5]),
            'vmstat_si': int(cols[6]),
            'vmstat_so': int(cols[7]),
            'vmstat_bi': int(cols[8]),
            'vmstat_bo': int(cols[9]),
            'vmstat_in': int(cols[10]),
            'vmstat_cs': int(cols[11]),
            'vmstat_us': int(cols[12]),
            'vmstat_sy': int(cols[13]),
            'vmstat_id': int(cols[14]),
            'vmstat_wa': int(cols[15]),
            'vmstat_st': int(cols[16]),
        }

        # make a timezone aware timestamp
        ts = cols[17] + ' ' + cols[18]
        tstmp = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')

        try:
            tz = getattr(pytz, VMSTAT_TIMEZONE.lower())
        except AttributeError as e:
            tz = pytz.timezone(VMSTAT_TIMEZONE.upper())

        tzts = datetime.datetime(tstmp.year, tstmp.month, tstmp.day, tstmp.hour, tstmp.minute, tstmp.second, tzinfo=tz)

        data['ts'] = tzts.timestamp()
        rows.append(data)

    return rows



def main():

    #obs = get_observations_from_delphiki()
    obs = get_observations_from_baseline()
    #vmstat_obs = get_vmstats()
    #fn = None
    fn = sys.argv[1]

    hostnames = [x['host'] for x in obs if x.get('host')]
    hostnames = sorted(set(hostnames))
    logger.info('%s hostnames found' % len(hostnames))
    hostmap = {}
    for row in obs:
        if not row.get('host'):
            continue
        if not row['host'][0].isalpha():
            continue
        if row['host'] not in hostmap or hostmap[row['host']] > row['ts']:
            hostmap[row['host']] = row['ts']
    #import epdb; epdb.st()
    hostnames = sorted(hostmap, key=lambda x: x[1])

    # need to know total duration
    t0 = min([x['ts'] for x in obs])
    tN = max([x['ts'] for x in obs])
    tT = tN - t0
    #tT = 40
    tT = 100
    logger.info('%ss total time' % tT)

    colors = ['red', 'lightgreen', 'lightblue', 'orange', 'purple', 'yellow']
    height = 700

    # make width normalized and relative to duration
    #width = (tT * 100) / 2
    #width = 1500
    width = 3000

    lpad = 5
    rpad = 2.5
    tpad = 10
    bpad = 5
    tD = tT / (100 - lpad - rpad)

    # the main drawing object
    dwg = svgwrite.Drawing('graph.svg', (width, height), debug=True)
    # black is prettier
    dwg.add(dwg.rect(size=('100%','100%'), class_='background', fill='black'))
    # note which file this was
    pg = dwg.add(dwg.g(font_size=10, stroke='white'))
    pg.add(dwg.text(fn, (pc(lpad/2), pc(tpad/2))))

    # the main timeseries border
    axiis = dwg.add(dwg.g(id='axiis', stroke='white'))
    # top
    axiis.add(dwg.line(start=(pc(lpad),pc(tpad)), end=(pc(100-rpad), pc(tpad))))
    # left
    axiis.add(dwg.line(start=(pc(lpad),pc(tpad)), end=(pc(lpad), pc(100-bpad))))
    # right
    axiis.add(dwg.line(start=(pc(100-rpad),pc(tpad)), end=(pc(100-rpad), pc(100-bpad))))
    # bottom
    axiis.add(dwg.line(start=(pc(lpad),pc(100-bpad)), end=(pc(100-rpad), pc(100-bpad))))

    # make a division for each host
    hostdivs = {}
    hostdivs_bin = (100 - tpad - bpad) / (len(hostnames) + 1)

    # mark each host and a line for it
    _axiis = dwg.add(dwg.g(id='axiis', stroke='lightgray'))
    y = tpad + hostdivs_bin
    for idh,hn in enumerate(hostnames):
        hostdivs[hn] = y
        #_axiis.add(dwg.line(start=(pc(lpad), pc(y)), end=(pc(100-rpad), pc(y))))
        pg = dwg.add(dwg.g(font_size=8, stroke='white'))
        pg.add(dwg.text(hn + ' ' + str(idh), (pc(lpad-3), pc(y))))
        y += hostdivs_bin

    # mark each task start
    taskmap = {}
    _colors = colors[:]
    thistask = None
    taskcount = 0
    totalrows = len(obs)
    for idr,row in enumerate(obs):
        if row.get('task_name'):
            tn = row.get('task_name')
            ts = row['ts']
            if not thistask or thistask != tn:
                # set the color
                if not _colors:
                    _colors = colors[:]
                taskmap[tn] = _colors[0]
                _colors.remove(_colors[0])
                thistask = tn
                taskcount += 1
                logger.info('[%s] task-%s %s' % (ts, taskcount, tn))

                # find x position
                xp = lpad + ((ts - t0) / tD)

                # label header
                pg = dwg.add(dwg.g(font_size=8, stroke=taskmap[tn]))
                pg.add(dwg.text('task-%s' % taskcount, (pc(xp+.1), pc(tpad-2))))
                # label footer
                pg.add(dwg.text('%s' % round((ts-t0), 4), (pc(xp+.1), pc(100-bpad+2))))

                # divline
                _axiis = dwg.add(dwg.g(id='axiis', stroke=taskmap[tn]))
                _axiis.add(dwg.line(start=(pc(xp),pc(tpad-2)), end=(pc(xp),pc(100-bpad+2))))

    logger.info('%s total tasks' % taskcount)

    # mark the final time
    xp = lpad + ((tN -t0)/ tD)
    _axiis = dwg.add(dwg.g(id='axiis', stroke='gray'))
    _axiis.add(dwg.line(start=(pc(xp),pc(tpad-2)), end=(pc(xp),pc(100-bpad+2))))

    # mark each host start+stop per task
    threshold = 60.0
    total = 0
    marks = []
    for hn in hostnames:
        lastts = None
        lastmark = None
        for idr,row in enumerate(obs):
            if row['host'] != hn:
                continue

            if not row['task_name']:
                continue

            ts = row['ts']
            xpos = lpad + ((ts - t0) / tD)
            ypos = hostdivs[hn]

            if lastmark is None:
                lastmark = (xpos, ypos)
                continue

            # what color?
            tc = taskmap[row['task_name']]
            #_axiis = dwg.add(dwg.g(id='axiis', stroke=tc, stroke_width=pc(hostdivs_bin * .4)))
            _axiis = dwg.add(dwg.g(id='axiis', stroke=tc))
            _axiis.add(dwg.line(start=(pc(lastmark[0]), pc(lastmark[1])), end=(pc(xpos), pc(ypos))))

            marks.append(
                ((pc(lastmark[0]), pc(lastmark[1])), (pc(xpos), pc(ypos)))
            )

            '''
            xtotal = xpos - lastmark[0]
            xtotal = round((xtotal / tT) * 100, 2)
            #print(xtotal)
            if xtotal > 2:
                pg = dwg.add(dwg.g(font_size=8, stroke='white'))
                pg.add(dwg.text('%s%%' % xtotal, (pc(xpos-1), pc(ypos))))
            #import epdb; epdb.st()
            '''

            lastmark = None
            total += 1

    #import epdb; epdb.st()
    dwg.save()



if __name__ == "__main__":
    main()
