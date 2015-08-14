# -*- coding: utf-8 -*-
import json

from lymph.client import Client
from lymph.cli.base import Command


class DiscoverCommand(Command):
    """
    Usage: lymph discover [--instances] [--ip=<address> | --guess-external-ip | -g] [--only-running] [options]

    Shows available services

    Options:

      --instances                  Show service instances.
      --json                       Output json.
      --full                       Show all published instance meta data.
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --only-running               Show only running services.

    {COMMON_OPTIONS}
    """

    short_description = 'Shows available services'

    def run(self):
        client = Client.from_config(self.config)
        services = client.container.discover()
        instances = {}
        for interface_name in sorted(services):
            service = client.container.lookup(interface_name)
            if not service and self.args.get('--only-running'):
                continue
            instances[interface_name] = service
        if self.args.get('--json'):
            print(json.dumps({
                name: [instance.serialize() for instance in service] for name, service in instances.items()
            }))
        else:
            self.print_human_readable_output(instances)

    def print_human_readable_output(self, instances):
        if instances:
            for interface_name, service in instances.items():
                print(u"%s [%s]" % (self.terminal.red(interface_name), len(service)))
                if self.args.get('--instances'):
                    service_instances = sorted(service, key=lambda d: d.identity)
                    for i, d in enumerate(service_instances):
                        prefix = u'└─' if i == len(service_instances) - 1 else u'├─'
                        print(u'%s [%s] %s' % (prefix, d.identity[:10], d.endpoint))
                        if self.args.get('--full'):
                            for k, v in sorted(d.serialize().items()):
                                if k == 'endpoint':
                                    continue
                                print(u'   %s: %r' % (k, v))
        else:
            print(u"No registered services found")
