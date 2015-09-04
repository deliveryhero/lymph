import logging
import os
from functools import partial
import signal
import sys

import gevent
from setproctitle import setproctitle
import six

from lymph.utils import import_object, dump_stacks
from lymph.autoreload import set_source_change_callback
from lymph.cli.base import Command
from lymph.core.container import create_container, InterfaceSkipped
from lymph.utils.sockets import get_unused_port


logger = logging.getLogger(__name__)


SIGNAL_NAMES = {getattr(signal, name): name for name in dir(signal) if name.startswith('SIG') and '_' not in name}


def install_plugins(container, plugins):
    for name, plugin_config in six.iteritems(plugins):
        cls = import_object(plugin_config['class'])
        container.install_plugin(cls, **plugin_config)


def install_interfaces(container, interfaces):
    for name, instance_config in six.iteritems(interfaces):
        try:
            cls_name = instance_config['class']
        except KeyError:
            print("no instance class for '%s'" % name)
            sys.exit(1)
        cls = import_object(cls_name)
        try:
            interface = container.install_interface(cls, name=name)
        except InterfaceSkipped as e:
            logger.info("skipping interface %s: %s", name, e)
            continue

        interface.apply_config(instance_config)


class InstanceCommand(Command):
    """
    Usage: lymph instance [--ip=<address> | --guess-external-ip | -g]
                         [--port <port> | -p <port>] [--reload] [--debug]
                         [--interface=<cls>]... [options]

    Runs a single service instance

    {INSTANCE_OPTIONS}

    {COMMON_OPTIONS}
    """

    proctitle = 'lymph-instance'
    short_description = 'Runs a single service instance'

    worker = False

    def run(self):
        debug = self.args.get('--debug')

        self._setup_container(debug)

        if debug:
            self._start_backdoor_terminal()

        self._register_signals()

        self.container.start(register=not self.args.get('--isolated', False))

        self._set_process_title()

        if self.args.get('--reload'):
            set_source_change_callback(self.container.stop)

        self.container.join()

    def _setup_container(self, debug):
        self.container = create_container(self.config, worker=self.worker)
        self.container.debug = debug
        # Set global exception hook to send unhandled exception to the container's error_hook.
        sys.excepthook = self.container.excepthook

        install_plugins(self.container, self.config.get('plugins', {}))
        install_interfaces(self.container, self.config.get('interfaces', {}))

        for cls_name in self.args.get('--interface', ()):
            cls = import_object(cls_name)
            self.container.install_interface(cls)

    def _start_backdoor_terminal(self):
        # XXX(Mouad): Imported here since this is still broken in Python3.x
        from gevent.backdoor import BackdoorServer

        try:
            ip = self.config.get_raw('debug.backdoor_ip')
        except KeyError:
            ip = '127.0.0.1'
        port = get_unused_port()
        endpoint = '%s:%s' % (ip, port)

        banner = "Welcome to backdoor Terminal of %s" % self.container.service_name

        backdoor = BackdoorServer(
            endpoint,
            locals={'container': self.container, 'dump_stacks': dump_stacks},
            banner=banner)
        gevent.spawn(backdoor.serve_forever)

        self.container.backdoor_endpoint = endpoint

    def _register_signals(self):
        gevent.signal(signal.SIGINT, self._handle_termination_signal, signal.SIGINT)
        gevent.signal(signal.SIGTERM, self._handle_termination_signal, signal.SIGTERM)
        gevent.signal(signal.SIGQUIT, self._handle_termination_signal, signal.SIGQUIT, prehook=partial(dump_stacks, output=sys.stderr.write))

    def _handle_termination_signal(self, signalnum, prehook=None):
        logger.info('caught %s, pid=%s', SIGNAL_NAMES.get(signalnum, signalnum), os.getpid())
        if prehook:
            prehook()
        self.container.stop(signalnum=signalnum)
        self.container.join()
        sys.exit(0)

    def _set_process_title(self):
        setproctitle('lymph-instance (identity: %s, endpoint: %s, config: %s)' % (
            self.container.identity,
            self.container.endpoint,
            self.config.source,
        ))


class WorkerCommand(InstanceCommand):
    """
    Usage: lymph worker [options]

    Runs a single worker instance.

    {INSTANCE_OPTIONS}

    {COMMON_OPTIONS}
    """    

    proctitle = 'lymph-worker'
    short_description = 'Runs a worker instance'

    worker = True


class NodeCommand(InstanceCommand):
    """
    Usage: lymph node [--debug] [options]

    Runs a node service that manages a group of processes on the same machine

    {INSTANCE_OPTIONS}

    {COMMON_OPTIONS}
    """

    proctitle = 'lymph-node'
    short_description = 'Runs a node service that manages a group of processes on the same machine'

    def run(self):
        self.config.update({
            'interfaces': {
                'node': {
                    'class': 'lymph.services.node:Node',
                    'instances': self.config.get_raw('instances', {}),
                    'sockets': self.config.get_raw('sockets', {}),
                },
            }
        })
        os.environ['LYMPH_NODE_CONFIG'] = self.config.source
        super(NodeCommand, self).run()

