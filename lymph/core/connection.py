# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import gevent
import math
import os
import time
import logging

from lymph.utils import SampleWindow
from lymph.exceptions import RpcError

logger = logging.getLogger(__name__)

UNKNOWN = 'unknown'
RESPONSIVE = 'responsive'
UNRESPONSIVE = 'unresponsive'
CLOSED = 'closed'
IDLE = 'idle'


class Connection(object):
    def __init__(self, server, endpoint, heartbeat_interval=1, timeout=1, idle_timeout=10, unresponsive_disconnect=30, idle_disconnect=60):
        self.server = server
        self.endpoint = endpoint
        self.timeout = timeout
        self.heartbeat_interval = heartbeat_interval
        self.idle_timeout = idle_timeout
        self.unresponsive_disconnect = unresponsive_disconnect
        self.idle_disconnect = idle_disconnect

        now = time.monotonic()
        self.last_seen = 0
        self.idle_since = 0
        self.last_message = now
        self.created_at = now
        self.heartbeat_samples = SampleWindow(100, factor=1000)  # milliseconds
        self.explicit_heartbeat_count = 0
        self.status = UNKNOWN

        self.received_message_count = 0
        self.sent_message_count = 0

        self.heartbeat_loop_greenlet = self.server.container.spawn(self.heartbeat_loop)
        self.live_check_loop_greenlet = self.server.container.spawn(self.live_check_loop)

    def __str__(self):
        return "connection to=%s last_seen=%s" % (self.endpoint, self._dt())

    def _dt(self):
        return time.monotonic() - self.last_seen

    @property
    def phi(self):
        p = self.heartbeat_samples.p(self._dt())
        if p == 0:
            return float('inf')
        return -math.log10(p)

    def set_status(self, status):
        self.status = status

    def heartbeat_loop(self):
        while True:
            start = time.monotonic()
            channel = self.server.ping(self.endpoint)
            try:
                channel.get(timeout=self.heartbeat_interval)
            except RpcError:
                pass
            else:
                self.heartbeat_samples.add(time.monotonic() - start)
                self.explicit_heartbeat_count += 1
            gevent.sleep(self.heartbeat_interval)

    def live_check_loop(self):
        while True:
            if self.last_seen:
                now = time.monotonic()
                if now - self.last_seen >= self.timeout:
                    self.set_status(UNRESPONSIVE)
                elif now - self.last_message >= self.idle_timeout:
                    self.set_status(IDLE)
                    self.idle_since = now
                else:
                    self.set_status(RESPONSIVE)
            roundtrip_stats = 'window (mean rtt = {mean:.1f} ms; stddev rtt = {stddev:.1f})'.format(**self.heartbeat_samples.stats)
            roundtrip_total_stats = 'total (mean rtt = {mean:.1f} ms; stddev rtt = {stddev:.1f})'.format(**self.heartbeat_samples.total.stats)
            logger.debug("pid=%s; %s; %s; phi = %.3f; ping/s = %.2f; status=%s" % (
                os.getpid(),
                roundtrip_stats,
                roundtrip_total_stats,
                self.phi,
                self.explicit_heartbeat_count / max(1, time.monotonic() - self.created_at),
                self.status,
            ))
            gevent.sleep(self.timeout)

    def close(self):
        if self.status == CLOSED:
            return
        self.status = CLOSED
        self.heartbeat_loop_greenlet.kill()
        self.live_check_loop_greenlet.kill()
        self.server.disconnect(self.endpoint)

    def on_recv(self, msg):
        now = time.monotonic()
        if not msg.is_idle_chatter():
            self.last_message = now
        self.received_message_count += 1

    def on_send(self, msg):
        if not msg.is_idle_chatter():
            self.last_message = time.monotonic()
        self.sent_message_count += 1

    def is_alive(self):
        return self.status in (RESPONSIVE, IDLE)

    def stats(self):
        return {
            'endpoint': self.endpoint,
            'rtt': self.heartbeat_samples.stats,
            'phi': self.phi,
            'status': self.status,
            'sent': self.sent_message_count,
            'received': self.received_message_count,
        }
