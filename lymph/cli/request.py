# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import logging
import math
import pprint
import sys
import time

from gevent.pool import Pool

from lymph.client import Client
from lymph.exceptions import Timeout
from lymph.cli.base import Command, handle_request_errors
from lymph.core import trace


logger = logging.getLogger(__name__)


class RequestCommand(Command):
    """
    Usage: lymph request [options] <subject> <params> [-]

    Sends a single RPC request to a service and outputs the response

    Parameters have to be JSON encoded

    Options:
      --ip=<address>               Use this IP for all sockets.
      --guess-external-ip, -g      Guess the public facing IP of this machine and
                                   use it instead of the provided address.
      --timeout=<seconds>          RPC timeout. [default: 2.0]
      --address=<addr>             Send the request to the given instance.
      --trace-id=<trace_id>        Use the given trace_id.
      -N <number>                  Send a total of <N> requests [default: 1].
      -C <concurrency>             Send requests from <concurrency> concurrent greenlets [default: 1].

    {COMMON_OPTIONS}
    """

    short_description = 'Sends a single RPC request to a service and outputs the response'

    def _run_one_request(self, request):
        pprint.pprint(request().body)

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
        stddev = math.sqrt(sum((t - avg) ** 2 for t in timings)) / n_success

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
        params = self.args.get('<params>')
        if params == '-':
            params = sys.stdin.read()
        body = json.loads(params)
        try:
            timeout = float(self.args.get('--timeout'))
        except ValueError:
            print("--timeout requires a number (e.g. --timeout=0.42)")
            return 1
        subject = self.args['<subject>']
        address = self.args.get('--address')
        if not address:
            address = subject.rsplit('.', 1)[0]

        client = Client.from_config(self.config)

        def request():
            trace.set_id(self.args.get('--trace-id'))
            return client.request(address, subject, body, timeout=timeout)

        N, C = int(self.args['-N']), int(self.args['-C'])

        if N == 1:
            return self._run_one_request(request)
        else:
            return self._run_many_requests(request, N, C)
