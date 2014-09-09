# -*- coding: utf-8 -*-
import json
import textwrap
import sys
import logging

import lymph
from lymph.client import Client
from lymph.exceptions import LookupFailure
from lymph.cli.base import Command


logger = logging.getLogger(__name__)


class RequestCommand(Command):
    """
    Usage: lymph request [options] [--ip=<address> | --guess-external-ip | -g] <address> <func> <params>

    Description:
        Sends a single RPC request to <address>. Parameters have to be JSON encoded.

    Options:
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --timeout=<seconds>          RPC timeout. [default: 2.0]

    {COMMON_OPTIONS}
    """

    short_description = 'Send a request message to some service and output the reply.'

    def run(self, **kwargs):
        client = Client.from_config(self.config, **kwargs)
        body = json.loads(self.args.get('<params>', '{}'))
        try:
            timeout = float(self.args.get('--timeout'))
        except ValueError:
            print("--timeout requires a number number (e.g. --timeout=0.42)")
            return 1
        response = client.request(self.args['<address>'], self.args['<func>'], body, timeout=timeout)
        print(response.body)


class InspectCommand(Command):
    """
    Usage: lymph inspect [--ip=<address> | --guess-external-ip | -g] <address> [options]

    Options:
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.

    {COMMON_OPTIONS}

    """

    short_description = 'Describe the available rpc methods of a service.'

    def run(self):
        client = Client.from_config(self.config)
        address = self.args['<address>']
        try:
            result = client.request(address, 'lymph.inspect', {}).body
        except LookupFailure:
            logger.error("cannot resolve %s", address)
            sys.exit(1)
        print
        for method in result['methods']:
            print("rpc {name}({params})\n    {help}\n".format(
                name=self.terminal.red(method['name']),
                params=', '.join(method['params']),
                help='\n    '.join(textwrap.wrap(method['help'], 70)),
            ))


class DiscoverCommand(Command):
    """
    Usage: lymph discover [--instances] [--ip=<address> | --guess-external-ip | -g] [options]

    Show available services

    Options:

      --instances                  Show service instances.
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.

    {COMMON_OPTIONS}

    """

    short_description = 'Show available services.'

    def run(self):
        client = Client.from_config(self.config)
        services = client.container.discover()
        if services:
            for service_type in sorted(services):
                p = client.container.lookup('lymph://%s' % service_type)
                print(u"%s [%s]" % (self.terminal.red(service_type), len(p)))
                if self.args.get('--instances'):
                    instances = sorted(p, key=lambda d: d.identity)
                    for i, d in enumerate(p):
                        prefix = u'└─' if i == len(instances) - 1 else u'├─'
                        print(u'%s [%s] %s' % (prefix, d.identity[:10], d.endpoint))
        else:
            print(u"No registered services found")


class SubscribeCommand(Command):
    """
    Usage: lymph subscribe <event-type>... [options]

    {COMMON_OPTIONS}
    """

    short_description = 'Prints events to stdout.'

    def run(self):
        event_type = self.args.get('<event-type>')

        class Subscriber(lymph.Interface):
            @lymph.event(*event_type)
            def on_event(self, event):
                print('%s: %r' % (event.evt_type, event.body))

        client = Client.from_config(self.config, interface_cls=Subscriber)
        client.container.join()


class EmitCommand(Command):
    """
    Usage: lymph emit <event-type> [<body>]

    {COMMON_OPTIONS}
    """

    short_description = 'Manually emits an event.'

    def run(self):
        event_type = self.args.get('<event-type>')
        body = json.loads(self.args.get('<body>'))

        client = Client.from_config(self.config)
        client.emit(event_type, body)
