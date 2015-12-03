# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import sys

from lymph.client import Client
from lymph.cli.base import Command


class DiscoverCommand(Command):
    """
    Usage: lymph discover [<name>] [--instances] [--ip=<address> | --guess-external-ip | -g] [--only-running] [options]

    Shows available services

    Options:

      --instances                  Show service instances.
      --json                       Output json.
      --full                       Show all published instance meta data.
      --all                        Show services without instances.
      --versions                   Show available versions.
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --only-running               DEPRECATED

    {COMMON_OPTIONS}
    """

    short_description = 'Shows available services'

    def run(self):
        if self.args.get('--only-running'):
            sys.stderr.write("\n--only-running is deprecated (it's now the default)\n\n")
        client = Client.from_config(self.config)

        name = self.args.get('<name>')
        if name:
            services = {name}
            self.args['--instances'] = True
        else:
            services = client.container.discover()

        instances = {}
        for interface_name in services:
            service = client.container.lookup(interface_name)
            if not service and not self.args.get('--all'):
                continue
            instances[interface_name] = service

        if self.args.get('--json'):
            print(json.dumps({
                name: [instance.serialize() for instance in service] for name, service in instances.items()
            }))
        else:
            self.print_human_readable_output(instances)

    def print_service_label(self, label, instances):
        instance_count = len({instance.identity for instance in instances})
        print(u"%s [%s]" % (self.terminal.red(label), instance_count))

    def print_service_instances(self, instances):
        if not self.args.get('--instances'):
            return
        for d in sorted(instances, key=lambda d: d.identity):
            print(u'[%s]  %-11s  %s' % (d.identity[:10], d.version if d.version else u'–', d.endpoint))
            if self.args.get('--full'):
                for k, v in sorted(d.serialize().items()):
                    if k == 'endpoint':
                        continue
                    print(u'   %s: %r' % (k, v))
        print()

    def print_human_readable_output(self, instances):
        if instances:
            for interface_name, service in sorted(instances.items()):
                if self.args.get('--versions'):
                    instances_by_version = {}
                    for instance in service:
                        instances_by_version.setdefault(instance.version, []).append(instance)
                    for version in sorted(instances_by_version.keys()):
                        self.print_service_label('%s@%s' % (service.name, version), instances_by_version[version])
                        self.print_service_instances(instances_by_version[version])
                else:
                    self.print_service_label(service.name, service)
                    self.print_service_instances(service)
        else:
            print(u"No registered services found")
