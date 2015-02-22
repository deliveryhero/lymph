# -*- coding: utf-8 -*-
from __future__ import print_function
import functools
import json
import textwrap
import time
import logging
import math
import sys

from gevent.pool import Pool

import lymph
from lymph.client import Client
from lymph.exceptions import LookupFailure, Timeout
from lymph.cli.base import Command


logger = logging.getLogger(__name__)


def handle_request_errors(func):
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except LookupFailure as e:
            logger.error("The specified service name could not be found: %s: %s" % (type(e).__name__, e))
            return 1
        except Timeout:
            logger.error("The request timed out. Either the service is not available or busy.")
            return 1
    return decorated


class RequestCommand(Command):
    """
    Usage: lymph request [options] <subject> <params>

    Description:
        Sends a single RPC request to <address>. Parameters have to be JSON encoded.

    Options:
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --timeout=<seconds>          RPC timeout. [default: 2.0]
      --address=<addr>             Send the request to the given instance.
      -N <number>                  Send a total of <N> requests [default: 1].
      -C <concurrency>             Send requests from <concurrency> concurrent greenlets [default: 1].

    {COMMON_OPTIONS}
    """

    short_description = 'Send a request message to some service and output the reply.'

    def _run_one_request(self, request):
        print(request().body)

    def _run_many_requests(self, request, n, c):
        # one warm up request for lookup and connection creation
        request()

        timings = []
        timeouts = []

        def timed_request(i):
            start = time.time()
            try:
                request()
            except Timeout:
                timeouts.append(i)
            else:
                timings.append(1000 * (time.time() - start))
            request_count = len(timings) + len(timeouts)
            if request_count % (n / 80) == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

        pool = Pool(size=c)
        print("sending %i requests, concurrency %i" % (n, c))
        start = time.time()
        pool.map(timed_request, range(n))
        total_time = (time.time() - start)

        timings.sort()
        n_success = len(timings)
        n_timeout = len(timeouts)
        avg = sum(timings) / n_success
        stddev = math.sqrt(sum((t - avg)**2 for t in timings)) / n_success

        print()
        print('Requests per second:   %8.2f Hz  (#req=%s)' % (n_success / total_time, n_success))
        print('Mean time per request: %8.2f ms  (stddev=%.2f)' % (avg, stddev))
        print('Timeout rate:          %8.2f %%   (#req=%s)' % (100 * n_timeout / float(n), n_timeout))
        print('Total time:            %8.2f s' % total_time)
        print()

        print('Percentiles:')
        print('  0.0 %%   %8.2f ms (min)' % timings[0])
        for p in (50, 90, 95, 97, 98, 99, 99.5, 99.9):
            print('%5.1f %%   %8.2f ms' % (p, timings[int(math.floor(0.01 * p * n_success))]))
        print('100.0 %%   %8.2f ms (max)' % timings[-1])

    @handle_request_errors
    def run(self):
        body = json.loads(self.args.get('<params>', '{}'))
        try:
            timeout = float(self.args.get('--timeout'))
        except ValueError:
            print("--timeout requires a number (e.g. --timeout=0.42)")
            return 1
        subject = self.args['<subject>']
        address = self.args.get('--address')
        if not address:
            address = subject.split('.', 1)[0]

        client = Client.from_config(self.config)

        def request():
            return client.request(address, subject, body, timeout=timeout)

        N, C = int(self.args['-N']), int(self.args['-C'])

        if N == 1:
            return self._run_one_request(request)
        else:
            return self._run_many_requests(request, N, C)



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

    @handle_request_errors
    def run(self):
        client = Client.from_config(self.config)
        result = client.request(self.args['<address>'], 'lymph.inspect', {}, timeout=5).body
        print()

        for method in sorted(result['methods'], key=lambda m: m['name']):
            print("rpc {name}({params})\n    {help}\n".format(
                name=self.terminal.red(method['name']),
                params=', '.join(method['params']),
                help='\n    '.join(textwrap.wrap(method['help'], 70)),
            ))


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
    Usage: lymph emit <event-type> [<body>] [options]

    {COMMON_OPTIONS}
    """

    short_description = 'Manually emits an event.'

    def run(self):
        event_type = self.args.get('<event-type>')
        body = json.loads(self.args.get('<body>'))

        client = Client.from_config(self.config)
        client.emit(event_type, body)
