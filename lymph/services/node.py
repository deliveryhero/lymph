import json
import logging
import gevent
import os
import psutil
import six
from gevent import subprocess
from six.moves import range

from lymph.core.interfaces import Interface
from lymph.utils.sockets import create_socket


logger = logging.getLogger(__name__)


class Process(object):
    def __init__(self, cmd, env=None):
        self.cmd = cmd
        self.env = env
        self._process = None
        self._popen = None

    def is_running(self):
        return self._process and self._process.is_running()

    def start(self):
        self._popen = subprocess.Popen(
            self.cmd, env=self.env, close_fds=False)
        self._process = psutil.Process(self._popen.pid)

    def stop(self):
        try:
            self._process.terminate()
            self._process.wait()
        except psutil.NoSuchProcess:
            pass

    def restart(self):
        print("restarting %s" % self)
        self.stop()
        self.start()

    def stats(self):
        try:
            memory = self._process.memory_info()
            return {
                'memory': {'rss': memory.rss, 'vms': memory.vms},
                'cpu': self._process.cpu_percent(interval=2.0),
            }
        except psutil.NoSuchProcess:
            return {}


class Node(Interface):
    register_with_coordinator = False

    def __init__(self, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)
        self.sockets = {}
        self.processes = []
        self.running = False
        self._sockets = []
        self._services = []

    def stats(self):
        process_stats = []
        for p in self.processes:
            if not p.is_running():
                continue
            process_stats.append({
                'command': p.cmd,
                'stats': p.stats(),
            })
        return {'processes': process_stats}

    def apply_config(self, config):
        for name, c in six.iteritems(config.get('instances', {})):
            self._services.append((name, c.get('command'), c.get('numprocesses', 1)))
        for name, c in six.iteritems(config.get('sockets', {})):
            self._sockets.append((name, c.get('host'), c.get('port')))

    def on_start(self):
        self.create_shared_sockets()
        self.running = True
        shared_fds = json.dumps({port: s.fileno() for port, s in six.iteritems(self.sockets)})
        for service_type, cmd, num in self._services:
            env = os.environ.copy()
            env['LYMPH_NODE'] = self.container.endpoint
            env['LYMPH_NODE_IP'] = self.container.ip
            env['LYMPH_SHARED_SOCKET_FDS'] = shared_fds
            for i in range(num):
                p = Process(cmd.split(' '), env=env)
                self.processes.append(p)
                logger.info('starting %s', cmd)
                p.start()
        self.container.spawn(self.watch_processes)

    def on_stop(self):
        logger.info("waiting for all service processes to die ...")
        self.running = False
        for p in self.processes:
            p.stop()
        super(Node, self).on_stop()

    def create_shared_sockets(self):
        for name, host, port in self._sockets:
            sock = create_socket(
                '%s:%s' % (host or self.container.ip, port), inheritable=True)
            self.sockets[port] = sock

    def restart_all(self):
        for process in self.processes:
            process.stop()

    def watch_processes(self):
        while True:
            for process in self.processes:
                try:
                    status = process._process.status()
                except psutil.NoSuchProcess:
                    if self.running:
                        process.start()
                    continue
                if status in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                    if self.running:
                        process.restart()
            gevent.sleep(1)

