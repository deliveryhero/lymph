# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import textwrap
import logging

import lymph
from lymph.client import Client
from lymph.exceptions import LookupFailure
from lymph.cli.base import Command


logger = logging.getLogger(__name__)


class RequestError(Exception):
    pass


class RequestCommand(Command):
    """
    Usage: lymph request [options] [--ip=<address> | --guess-external-ip | -g] <subject> <params>

    Description:
        Sends a single RPC request to <address>. Parameters have to be JSON encoded.

    Options:
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --timeout=<seconds>          RPC timeout. [default: 2.0]
      --address=<addr>             Send the request to the given instance.

    {COMMON_OPTIONS}
    """

    short_description = 'Send a request message to some service and output the reply.'

    def _request(self, address, subject, body, timeout=2.0):
        client = Client.from_config(self.config)
        try:
            response = client.request(
                address,
                subject,
                body,
                timeout=timeout
            )
        except lymph.exceptions.LookupFailure as e:
            raise RequestError("The specified service name could not be found: %s: %s" % (type(e).__name__, e))
        except lymph.exceptions.Timeout:
            raise RequestError("The request timed out. Either the service is not available or busy.")
        return response.body

    def run(self):
        body = json.loads(self.args.get('<params>', '{}'))
        try:
            timeout = float(self.args.get('--timeout'))
        except ValueError:
            print("--timeout requires a number number (e.g. --timeout=0.42)")
            return 1
        subject = self.args['<subject>']
        address = self.args.get('--address')
        if not address:
            address = subject.split('.', 1)[0]
        try:
            result = self._request(address, subject, body, timeout=timeout)
        except RequestError as ex:
            logger.error(str(ex))
            return 1
        print(result)


class InspectCommand(RequestCommand):
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
        try:
            result = self._request(
                self.args['<address>'], 'lymph.inspect', {}, timeout=5)
        except RequestError as ex:
            logger.error(str(ex))
            return 1

        print()

        for method in sorted(result['methods'], key=lambda m: m['name']):
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
            for service_name in sorted(services):
                p = client.container.lookup(service_name)
                print(u"%s [%s]" % (self.terminal.red(service_name), len(p)))
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
