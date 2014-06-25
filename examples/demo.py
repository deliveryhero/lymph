from __future__ import print_function, unicode_literals

import random
import gevent
import lymph
from lymph.core import trace


class Client(lymph.Interface):
    service_type = 'demo'
    delay = .1

    def on_start(self):
        gevent.spawn(self.loop)

    @lymph.event('uppercase_transform_finished')
    def on_uppercase(self, event):
        echo = self.proxy('lymph://echo', timeout=2)
        print(echo.echo(text="DONE"), event.body)

    def apply_config(self, config):
        self.delay = config.get('delay', .1)

    def loop(self):
        i = 0
        echo = self.proxy('lymph://echo', timeout=2)
        while True:
            gevent.sleep(.1)
            trace.set_id()
            try:
                result = echo.upper(text='foo_%s' % i)
            except lymph.RpcError:
                continue
            print("result = %s" % result)
            i += 1
