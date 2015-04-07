# -*- coding: utf-8 -*-
from lymph.client import Client
from lymph.cli.base import Command


class DiscoverCommand(Command):
    """
    Usage: lymph discover [--instances] [--ip=<address> | --guess-external-ip | -g] [--only-running] [options]

    Show available services

    Options:

      --instances                  Show service instances.
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --only-running               Show only running services.

    {COMMON_OPTIONS}

    """

    short_description = 'Show available services.'

    def run(self):
        client = Client.from_config(self.config)
        services = client.container.discover()
        if services:
            for interface_name in sorted(services):
                interface_instances = client.container.lookup(interface_name)
                if not interface_instances and self.args.get('--only-running'):
                    continue
                print(u"%s [%s]" % (self.terminal.red(interface_name), len(interface_instances)))
                if self.args.get('--instances'):
                    instances = sorted(interface_instances, key=lambda d: d.identity)
                    for i, d in enumerate(interface_instances):
                        prefix = u'└─' if i == len(instances) - 1 else u'├─'
                        print(u'%s [%s] %s' % (prefix, d.identity[:10], d.endpoint))
        else:
            print(u"No registered services found")
