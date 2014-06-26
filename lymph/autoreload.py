import sys
import os
import gevent


def watch_modules(callback):
    modules = {}
    while True:
        for name, module in list(sys.modules.items()):
            if module is None or not hasattr(module, '__file__'):
                continue
            module_source_path = os.path.abspath(module.__file__).rstrip('c')
            try:
                stat = os.stat(module_source_path)
            except OSError:
                continue
            mtime = stat.st_mtime
            if name in modules and modules[name] != mtime:
                callback()
            modules[name] = mtime
        gevent.sleep(1)


def set_source_change_callback(callback):
    gevent.spawn(watch_modules, callback)
