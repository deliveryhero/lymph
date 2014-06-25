# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals

import gevent
import math
import os
import time
import logging

from lymph.utils import SampleWindow
from lymph.exceptions import RpcError


UNKNOWN = 'unknown'
RESPONSIVE = 'responsive'
UNRESPONSIVE = 'unresponsive'
CLOSED = 'closed'
IDLE = 'idle'

MIN_HEARTBEAT_INTERVAL = .01


logger = logging.getLogger(__name__)


class Connection(object):
    def __init__(self, container, endpoint, heartbeat_interval=1, timeout=1, idle_timeout=10, unresponsive_disconnect=30, idle_disconnect=60):
        self.container = container
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
        self.roundtrip_samples = SampleWindow(100, factor=1000)  # milliseconds
        self.explicit_heartbeat_count = 0
        self.status = UNKNOWN

        self.received_message_count = 0
        self.sent_message_count = 0

        self.heartbeat_loop_greenlet = self.container.spawn(self.heartbeat_loop)
        self.live_check_loop_greenlet = self.container.spawn(self.live_check_loop)

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
            channel = self.container.ping(self.endpoint)
            try:
                channel.get(timeout=self.heartbeat_interval)
            except RpcError:
                pass
            else:
                self.roundtrip_samples.add(time.monotonic() - start)
                self.explicit_heartbeat_count += 1
            gevent.sleep(max(self.heartbeat_interval - .001 * self.roundtrip_samples.mean, MIN_HEARTBEAT_INTERVAL))

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
            heartbeat_stats = 'window (mean ♡ = {mean:.1f} ms; stddev ♡ = {stddev:.1f})'.format(**self.heartbeat_samples.stats)
            heartbeat_total_stats = 'total (mean ♡ = {mean:.1f} ms; stddev ♡ = {stddev:.1f})'.format(**self.heartbeat_samples.total.stats)
            roundtrip_stats = 'mean rtt = {mean:.3f} ms; stddev rtt = {stddev:.3f}'.format(**self.roundtrip_samples.stats)
            logger.debug("pid=%s; %s; %s; %s; φ = %.3f; ping/s = %.2f; status=%s" % (
                os.getpid(),
                roundtrip_stats,
                heartbeat_stats,
                heartbeat_total_stats,
                self.phi,
                self.explicit_heartbeat_count / (time.monotonic() - self.created_at),
                self.status,
            ))
            gevent.sleep(self.timeout)

    def close(self):
        if self.status == CLOSED:
            return
        self.status = CLOSED
        self.heartbeat_loop_greenlet.kill()
        self.live_check_loop_greenlet.kill()
        self.container.disconnect(self.endpoint)

    def on_recv(self, msg):
        now = time.monotonic()
        if self.last_seen:
            self.heartbeat_samples.add(now - self.last_seen)
        self.last_seen = now
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
            'rtt': self.roundtrip_samples.stats,
            'heartbeat': self.heartbeat_samples.stats,
            'phi': self.phi,
            'status': self.status,
            'sent': self.sent_message_count,
            'received': self.received_message_count,
        }
