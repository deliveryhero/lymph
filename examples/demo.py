from __future__ import print_function, unicode_literals

import random
import gevent
import iris
from iris.core import trace


class Client(iris.Interface):
    service_type = 'demo'
    delay = 1

    def on_start(self):
        gevent.spawn(self.loop)

    @iris.event('uppercase_transform_finished')
    def on_uppercase(self, event):
        echo = self.proxy('iris://echo', timeout=2)
        print(echo.echo(text="DONE"), event.body)

    def apply_config(self, config):
        self.delay = config.get('delay', 1)

    def loop(self):
        i = 0
        echo = self.proxy('iris://echo', timeout=2)
        while True:
            gevent.sleep(self.delay)
            trace.set_id()
            try:
                result = echo.upper(text='foo_%s' % i)
            except iris.RpcError:
                continue
            print("result = %s" % result)
            i += 1
