import json
import logging
import gevent
import os
import psutil
import six
from gevent import subprocess
from six.moves import range

from lymph.core.interfaces import Interface
from lymph.core.monitoring.metrics import RawMetric
from lymph.utils.sockets import create_socket


logger = logging.getLogger(__name__)


class Process(object):
    def __init__(self, cmd, env=None, service_type='n/a'):
        self.cmd = cmd
        self.env = env
        self.service_type = service_type
        self._process = None
        self._popen = None

    def is_running(self):
        return self._process and self._process.is_running()

    def start(self):
        self._popen = subprocess.Popen(
            self.cmd, env=self.env, close_fds=False)
        self._process = psutil.Process(self._popen.pid)

    def stop(self, **kwargs):
        signalnum = kwargs.get('signalnum')
        try:
            if signalnum:
                self._process.send_signal(signalnum)
            else:
                self._process.terminate()
            self._process.wait()
        except psutil.NoSuchProcess:
            pass

    def restart(self):
        print("restarting %s" % self)
        self.stop()
        self.start()

    def _get_metrics(self):
        if not self.is_running():
            return
        try:
            memory = self._process.memory_info()
            yield RawMetric('node.process.memory.rss', memory.rss, {'service_type': self.service_type})
            yield RawMetric('node.process.memory.vms', memory.vms, {'service_type': self.service_type})
            cpu = self._process.cpu_percent(interval=2.0)
            yield RawMetric('node.process.cpu', cpu, {'service_type': self.service_type})
        except psutil.NoSuchProcess:
            pass


class Node(Interface):
    def __init__(self, *args, **kwargs):
        super(Node, self).__init__(*args, **kwargs)
        self.sockets = {}
        self.processes = []
        self.running = False
        self._sockets = []
        self._services = []

    def apply_config(self, config):
        for name, c in six.iteritems(config.get('instances', {})):
            self._services.append((name, c.get('command'), c.get('numprocesses', 1)))

        socket_config = config.get_raw('sockets', ())
        if isinstance(socket_config, dict):
            socket_config = socket_config.values()
        for c in socket_config:
            self._sockets.append((c.get('host'), c.get('port')))

    def on_start(self):
        self.create_shared_sockets()
        self.running = True
        shared_fds = json.dumps({port: s.fileno() for port, s in six.iteritems(self.sockets)})
        for service_type, cmd, num in self._services:
            env = os.environ.copy()
            env.update({
                'LYMPH_NODE': self.container.endpoint,
                'LYMPH_MONITOR': self.container.monitor.endpoint,
                'LYMPH_NODE_IP': self.container.server.ip,
                'LYMPH_SHARED_SOCKET_FDS': shared_fds,
                'LYMPH_SERVICE_NAME': service_type,
            })
            for i in range(num):
                p = Process(cmd.split(' '), env=env, service_type=service_type)
                self.processes.append(p)
                logger.info('starting %s', cmd)
                p.start()
        self.container.spawn(self.watch_processes)

    def on_stop(self, **kwargs):
        logger.info("waiting for all service processes to die ...")
        self.running = False
        for p in self.processes:
            p.stop(**kwargs)
        super(Node, self).on_stop(**kwargs)

    def create_shared_sockets(self):
        for host, port in self._sockets:
            sock = create_socket(
                '%s:%s' % (host or self.container.server.ip, port), inheritable=True)
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

    def _get_metrics(self):
        for process in self.processes:
            for metric in process._get_metrics():
                yield metric
