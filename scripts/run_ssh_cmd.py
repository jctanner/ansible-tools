#!/usr/bin/env python

# run_echo.py
#   A script to measure remote command execution speed with ansible
#
# usage:
#   python2 run_ssh_cmd.py
#
# examples:
#   python2 run_ssh_cmd.py \
#    --debug \
#    --use_plugin \
#    --username=vagrant \
#    --hostname=vagrant \
#    --iterations=100 \
#    --command="umask 77 && mkdir -p ~/.ansible_test && rm -rf ~/.ansible_test"

import fcntl
import json
import mock
import os
import re
import subprocess
import time

from datetime import datetime
from optparse import OptionParser

from ansible.compat import selectors
from ansible.errors import AnsibleError
from ansible.plugins.loader import connection_loader


HAS_LOGZERO = False
try:
    from logzero import logger
    HAS_LOGZERO = True
except ImportError:
    pass


class MockLogger(object):
    level = 'DEBUG'

    def setLevel(self, level):
        self.level = level

    def info(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)

    def debug(self, msg):
        if self.level == 'DEBUG':
            print(msg)

    @staticmethod
    def debug(msg, host=None):
        print(msg)

    @staticmethod
    def v(msg, host=None):
        print(msg)

    @staticmethod
    def vv(msg, host=None):
        print(msg)

    @staticmethod
    def vvv(msg, host=None):
        print(msg)

    @staticmethod
    def vvvv(msg, host=None):
        print(msg)

    @staticmethod
    def vvvvv(msg, host=None):
        print(msg)


class MockPlayContext(object):
    executable = '/bin/sh'
    shell = 'sh'
    ssh_executable = 'ssh'
    port = 22
    remote_user = 'vagrant'
    password = None
    _load_name = 'ssh'
    name = 'ssh'
    timeout = 10
    verbosity = 5
    ssh_args = None
    private_key_file = None
    prompt = None
    become = False


if not HAS_LOGZERO:
    print('PLEASE INSTALL LOGZERO FOR BEST EXPERIENCE')
    logger = MockLogger()


SSHCMD = [
  "/usr/bin/ssh",
  "-vvvvvv",
  "-C",
  "-o",
  "ControlMaster=auto",
  "-o",
  "ControlPersist=60s",
  "-o",
  "IdentityFile=\"~/.ssh/id_rsa\"",
  "-o",
  "KbdInteractiveAuthentication=no",
  "-o",
  "PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
  "-o",
  "PasswordAuthentication=no",
  "-o",
  "User=vagrant",
  "-o",
  "ConnectTimeout=10",
  "-o",
  "ControlPath=~/.ansible/cp/testcp",
  "el6host",
  "/bin/sh -c 'echo ~vagrant && sleep 0'"
]


def validate_control_socket(SSHCMD):
    # $ ssh -O check -o ControlPath=... vagrant@el6host
    # Master running (pid=24779)
    for idx, x in enumerate(SSHCMD):
        if x.startswith('ControlPath'):
            cppath = x.split('=')[1]

            if not os.path.exists(cppath):
                logger.info('%s does not exist' % cppath)
            else:
                cpcmd = SSHCMD[:-1]

                checkcmd = cpcmd[:]
                checkcmd.insert(-1, '-O')
                checkcmd.insert(-1, 'check')
                print('# %s' % ' '.join(checkcmd))
                (rc, so, se) = run_ssh_cmd(
                    ' '.join(checkcmd),
                    use_selectors=False
                )
                logger.debug('rc: %s' % rc)
                logger.debug('so: %s' % so)
                logger.debug('se: %s' % se)

                if rc != 0 or so.strip():
                    logger.info('checkcmd rc != 0 or has stdout')
                    logger.info(so)
                    logger.info(se)


def set_vcount(SSHCMD, count=None):
    if count is None:
        return SSHCMD

    isset = False
    for idx, x in enumerate(SSHCMD):
        if x.startswith('-v'):
            isset = True
            SSHCMD[idx] = '-' + ''.join(['v' for x in range(0, count)])

    if not isset:
        SSHCMD.insert(1, '-' + ''.join(['v' for x in range(0, count)]))

    return SSHCMD


def set_hostname(SSHCMD, hostname):
    SSHCMD[-2] = hostname
    return SSHCMD


def set_username(SSHCMD, username):
    for idx, x in enumerate(SSHCMD):
        if x.startswith('User='):
            SSHCMD[idx] = 'User=%s' % username
        if 'echo ~' in x:
            orig = re.search(r'~\w+', x).group()
            new = '~%s' % username
            SSHCMD[idx] = x.replace(orig, new, 1)
    return SSHCMD


def set_keyfile(SSHCMD, keyfile):
    # "IdentityFile=\"~/.ssh/id_rsa\"",
    for idx, x in enumerate(SSHCMD):
        if x.startswith('IdentityFile'):
            SSHCMD[idx] = 'IdentityFile="%s"' % keyfile
            break
    return SSHCMD


def remove_control_persist(SSHCMD):
    while True:
        if not [x for x in SSHCMD if x.startswith('Control')]:
            break

        for idx, x in enumerate(SSHCMD):
            if x.startswith('Control'):
                print('popping %s' % x)
                SSHCMD.pop(idx)
                SSHCMD.pop(idx-1)
                print(' '.join(SSHCMD))
                break

    return SSHCMD


def extract_speeed_from_stdtout(so):

    '''Strip transfer statistics from stderr/stdout'''

    # Transferred: sent 3192, received 2816 bytes, in 1.6 seconds
    # Bytes per second: sent 1960.0, received 1729.1
    data = {}
    for line in so.split('\n'):
        if 'Transferred' in line:
            sent = re.search(r'sent \d+', line).group()
            received = re.search(r'received \d+', line).group()
            duration = re.search(r'in \d+\.\d+', line).group()
            data['transfered'] = {
                'sent': float(sent.split()[1]),
                'received': float(received.split()[1]),
                'duration': float(duration.split()[1]),
            }

        elif 'Bytes per second' in line:
            sent = re.search(r'sent \d+', line).group()
            received = re.search(r'received \d+', line).group()
            data['speeds'] = {
                'sent': float(sent.split()[1]),
                'received': float(received.split()[1]),
            }

    return data


def run_ssh_exec(command=None, hostname=None, username=None, keyfile=None):

    '''Use ansible's connection plugin to execute the command'''

    with mock.patch('ansible.plugins.connection.ssh.display', MockLogger):
        pc = MockPlayContext()
        if hostname:
            pc.remote_addr = hostname
        if username:
            pc.remote_user = username
        if keyfile:
            pc.private_key_file = keyfile

        ssh = connection_loader.get('ssh', pc, None)
        (rc, so, se) = ssh.exec_command(command)

    return (
        rc,
        so.decode('utf-8'),
        se.decode('utf-8')
    )


def run_ssh_cmd(SSHCMD, command=None, hostname=None, username=None, use_selectors=False):

    '''Run the command with subprocess and communicate or selectors'''

    if not use_selectors:
        p = subprocess.Popen(
            ' '.join(SSHCMD),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        (so, se) = p.communicate()
        return (p.returncode, so.decode('utf-8'), se.decode('utf-8'))

    else:

        # This is kinda how ansible runs ssh commands ...

        logger.info('using selectors ...')
        p = subprocess.Popen(
            ' '.join(SSHCMD),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        for fd in (p.stdout, p.stderr):
            fcntl.fcntl(
                fd,
                fcntl.F_SETFL,
                fcntl.fcntl(
                    fd,
                    fcntl.F_GETFL
                ) | os.O_NONBLOCK
            )

        states = [
            'awaiting_prompt',
            'awaiting_escalation',
            'ready_to_send',
            'awaiting_exit'
        ]
        state = states.index('ready_to_send')
        state += 1

        selector = selectors.DefaultSelector()
        selector.register(p.stdout, selectors.EVENT_READ)
        selector.register(p.stderr, selectors.EVENT_READ)

        timeout = 0
        events = None

        b_stdout = b_stderr = b''
        b_tmp_stdout = b_tmp_stderr = b''

        try:

            counter = 0
            while True:
                counter += 1

                if counter == 1:
                    time.sleep(2)

                poll = p.poll()
                events = selector.select(timeout)

                if not events:
                    if state <= states.index('awaiting_escalation'):
                        if poll is not None:
                            break
                        p.terminate()
                        raise AnsibleError('timeout')

                for key, event in events:

                    if key.fileobj == p.stdout:
                        b_chunk = p.stdout.read()
                        logger.debug('b_chunk %s' % b_chunk)
                        if b_chunk == b'':
                            selector.unregister(p.stdout)
                            timeout = 1
                        b_tmp_stdout += b_chunk
                    elif key.fileobj == p.stderr:
                        b_chunk = p.stderr.read()
                        logger.debug('b_chunk %s' % b_chunk)
                        if b_chunk == b'':
                            selector.unregister(p.stderr)
                        b_tmp_stderr += b_chunk

                if state < states.index('ready_to_send'):
                    if b_tmp_stdout:
                        b_stdout += b_tmp_stdout
                    if b_tmp_stderr:
                        b_stderr += b_tmp_stderr
                else:
                    b_stdout += b_tmp_stdout
                    b_stderr += b_tmp_stderr
                    b_tmp_stdout = b_tmp_stderr = b''

                if states[state] == 'awaiting_prompt':
                    state += 1

                if states[state] == 'awaiting_escalation':
                    state += 1

                if states[state] == 'ready_to_send':
                    state += 1

                if poll is not None:
                    if not selector.get_map() or not events:
                        break
                    timeout = 0
                    continue

                elif not selector.get_map():
                    p.wait()
                    break

                logger.debug(counter)
                logger.debug(state)
                logger.debug(states[state])
                logger.debug(poll)
                logger.debug(selector.get_map())
                logger.debug(events)

        finally:
            selector.close()

        return (
            p.returncode,
            b_stdout.decode('utf-8'),
            b_stderr.decode('utf-8')
        )


##########################################
#   MAIN
##########################################

def main():

    global SSHCMD

    parser = OptionParser()
    parser.add_option('--iterations', type=int, default=10)
    parser.add_option('--controlpersist', action='store_true')
    parser.add_option('--selectors', action='store_true')
    parser.add_option('--use_plugin', action='store_true')
    parser.add_option('--vcount', type=int, default=None)
    parser.add_option('--debug', action='store_true')
    parser.add_option('--hostname', default=None)
    parser.add_option('--username', default=None)
    parser.add_option('--keyfile', default=None)
    parser.add_option('--command', default=None)
    (options, args) = parser.parse_args()

    if not options.debug:
        logger.setLevel('INFO')

    # munge the example ssh command if not using the connection plugin
    if not options.use_plugin:
        validate_control_socket(SSHCMD)
        if not options.controlpersist:
            SSHCMD = remove_control_persist(SSHCMD)

        if options.hostname:
            SSHCMD = set_hostname(SSHCMD, options.hostname)

        if options.username:
            SSHCMD = set_username(SSHCMD, options.username)

        if options.keyfile:
            SSHCMD = set_keyfile(SSHCMD, options.keyfile)

        if options.vcount is not None:
            SSHCMD = set_vcount(SSHCMD, count=options.vcount)

        if options.command is not None:
            SSHCMD[-1] = '/bin/sh -c "%s"' % options.command

        logger.info(SSHCMD)

    # run the command X times and record the durations + speeds
    durations = []
    for x in range(0, options.iterations):
        logger.info('iteration %s' % x)
        start = datetime.now()
        if options.use_plugin:
            (rc, so, se) = run_ssh_exec(
                command=options.command,
                hostname=options.hostname,
                username=options.username,
                keyfile=options.keyfile,
            )
        else:
            (rc, so, se) = run_ssh_cmd(
                SSHCMD,
                hostname=options.hostname,
                username=options.username,
                use_selectors=options.selectors
            )
        stop = datetime.now()
        durations.append(stop - start)
        stats = extract_speeed_from_stdtout(se)
        logger.info('transfer stats ...')
        for k, v in stats.items():
            for k2, v2 in v.items():
                logger.info('%s.%s = %s' % (k, k2, v2))
        logger.info('rc: %s' % rc)
        logger.info('so:%s' % so.strip())
        if rc != 0:
            logger.error(se)
            logger.error('sshcmd: %s' % ' '.join(SSHCMD))

    durations = [x.total_seconds() for x in durations]
    logger.info('durations ...')
    for idx, x in enumerate(durations):
        logger.info('%s. %s' % (idx, x))
    logger.info('duration min: %s' % min(durations))
    logger.info('duration max: %s' % max(durations))
    avg = sum(durations) / float(len(durations))
    logger.info('duration avg: %s' % avg)


if __name__ == "__main__":
    main()
