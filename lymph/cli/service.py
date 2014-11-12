import gevent
import logging
import os
import signal
import six
import sys
from setproctitle import setproctitle

from lymph.utils import import_object
from lymph.autoreload import set_source_change_callback
from lymph.cli.base import Command
from lymph.core.container import create_container


logger = logging.getLogger(__name__)


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
        cls.service_type = cls.service_type or name
        instance = container.install(cls)
        instance.apply_config(instance_config)


class InstanceCommand(Command):
    """
    Usage: lymph instance [--ip=<address> | --guess-external-ip | -g]
                         [--port <port> | -p <port>] [--reload] [--debug]
                         [--interface=<cls>]... [options]

    {INSTANCE_OPTIONS}

    {COMMON_OPTIONS}
    """

    short_description = 'Run a single service instance (one process).'

    def run(self):
        container = create_container(self.config)
        install_plugins(container, self.config.get('plugins', {}))
        install_interfaces(container, self.config.get('interfaces', {}))

        for cls_name in self.args.get('--interface', ()):
            cls = import_object(cls_name)
            container.install(cls)

        if self.args.get('--debug'):
            from gevent.backdoor import BackdoorServer
            backdoor = BackdoorServer(('127.0.0.1', 5005), locals={'container': container})
            gevent.spawn(backdoor.serve_forever)

        def handle_signal():
            logger.info('caught SIGINT/SIGTERM, pid=%s', os.getpid())
            container.stop()
            container.join()
            sys.exit(0)
        gevent.signal(signal.SIGINT, handle_signal)
        gevent.signal(signal.SIGTERM, handle_signal)

        setproctitle('lymph-instance (identity: %s, endpoint: %s, config: %s)' % (
            container.identity,
            container.endpoint,
            self.config.source,
        ))

        container.start(register=not self.args.get('--isolated', False))

        if self.args.get('--reload'):
            set_source_change_callback(container.stop)

        container.join()


class NodeCommand(InstanceCommand):
    """
    Usage: lymph node [--debug] [options]

    {INSTANCE_OPTIONS}

    {COMMON_OPTIONS}
    """

    short_description = 'Run a node service that manages a group of processes on the same machine.'

    def run(self):
        self.config.update({
            'interfaces': {
                'node': {
                    'class': 'lymph.services.node:Node',
                    'instances': self.config.get('instances', {}),
                    'sockets': self.config.get('sockets', {}),
                },
            }
        })
        os.environ['LYMPH_NODE_CONFIG'] = self.config.source
        super(NodeCommand, self).run()

