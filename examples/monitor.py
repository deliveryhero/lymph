# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import collections
import gevent
import json
import mimetypes
import msgpack
import six
import zmq.green as zmq

from lymph.web.interfaces import WebServiceInterface

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response


class Monitor(WebServiceInterface):
    http_port = 4044

    url_map = Map([
        Rule('/', endpoint='index'),
        Rule('/static/<path:path>', endpoint='static_resource'),
        Rule('/api/stats/', endpoint='get_stats'),
    ])

    def on_start(self):
        self._stats = {}
        self.monitor_endpoint = 'tcp://0.0.0.0:44044'
        super(Monitor, self).on_start()
        self.monitor_sub_socket = zmq.Context.instance().socket(zmq.SUB)
        self.monitor_sub_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.monitor_sub_socket.bind(self.monitor_endpoint)
        self.monitor_loop_greenlet = gevent.spawn(self.monitor_loop)

    def monitor_loop(self):
        while True:
            stats = self.monitor_sub_socket.recv_multipart()
            topic, data = stats
            data = msgpack.loads(data, encoding='utf-8')
            for conn in data['connections']:
                key = data['endpoint'], conn['endpoint']
                try:
                    conn_stats = self._stats[key]
                except KeyError:    
                    conn_stats = collections.deque(maxlen=100)
                    self._stats[key] = conn_stats
                conn_stats.append((data['time'], conn['rtt']['mean']))

    def static_resource(self, request, path=None, content_type=None):
        if not content_type:
            content_type, encoding = mimetypes.guess_type(path)
        with open('examples/static/%s' % path) as f:
            return Response(f.read(), content_type=content_type)

    def index(self, request):
        return self.static_resource(request, 'monitor.html', 'text/html')

    def get_stats(self, request):
        data = []
        i = 0
        for key, series in six.iteritems(self._stats):
            data.append({
                'name': u'–'.join(key),
                'data': [dict(x=t, y=hb) for t, hb in series],
            })
            i += 1
            #for t, hb in series:
        return Response(json.dumps(data), content_type='application/json')
