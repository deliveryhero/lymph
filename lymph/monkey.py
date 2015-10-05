

def patch():
    if patch._initialized:
        return
    patch._initialized = True

    import gevent.monkey
    gevent.monkey.patch_all()

    import sys
    if sys.version_info.major < 3:
        _py2_patches()

    _export()
patch._initialized = False


def _export():
    import lymph
    lymph.__version__ = '0.9.0'

    from lymph.exceptions import RpcError, LookupFailure, Timeout
    from lymph.core.decorators import rpc, raw_rpc, event, task
    from lymph.core.interfaces import Interface
    from lymph.core.declarations import proxy

    for obj in (RpcError, LookupFailure, Timeout, rpc, raw_rpc, event, Interface, proxy, task):
        setattr(lymph, obj.__name__, obj)


def _py2_patches():
    import monotime  # NOQA
