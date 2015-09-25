import abc
import collections
import functools
import inspect

import six

from lymph.core.declarations import Declaration


@six.add_metaclass(abc.ABCMeta)
class RPCBase(collections.Callable):
    """Base interface for RPC functions.

    Implementation of this interface can be used as decorator for
    functions/methods.

    Example ::

        >>> @Decorator
        ... def fibo(n):
        ...     "Fibonacci number."
        ...     if n <= 1: return n
        ...     return fibo(n-1) + fibo(n-2)
        ...
        >>> fibo.__doc__
        'Fibonacci number.'
        >>> fibo.__name__
        'fibo'
        >>> fibo(3)
        2
    """

    def __init__(self, func, assigned=functools.WRAPPER_ASSIGNMENTS):
        self.original = func
        self._func = func

        functools.update_wrapper(
            self, func, assigned=functools.WRAPPER_ASSIGNMENTS)

    @property
    def args(self):
        """Return original function argument spec skipping self.

        Returns:
          ``inspect.ArgSpec``.
        """
        spec = inspect.getargspec(self._func)
        return inspect.ArgSpec(spec.args[1:], *spec[1:])

    def __get__(self, obj, obj_type=None):
        if obj is None:
            return self
        return functools.partial(self._func, obj)

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    @abc.abstractmethod
    def rpc_call(self, interface, channel, *args, **kwargs):
        pass

    def decorate(self, decorator):
        self._func = decorator(self._func)


class _RawRPCDecorator(RPCBase):

    @property
    def args(self):
        # Skip channel in the arguments spec.
        spec = super(_RawRPCDecorator, self).args
        return inspect.ArgSpec(spec.args[1:], *spec[1:])

    def rpc_call(self, interface, channel, *args, **kwargs):
        return self._func(interface, channel, *args, **kwargs)


class _RPCDecorator(RPCBase):

    def __init__(self, *args, **kwargs):
        self._raises = kwargs.pop('raises', ())
        super(_RPCDecorator, self).__init__(*args, **kwargs)

    @property
    def raises(self):
        return self._raises

    def rpc_call(self, interface, channel, *args, **kwargs):
        try:
            ret = self._func(interface, *args, **kwargs)
        except self._raises as ex:
            channel.error(type=ex.__class__.__name__, message=str(ex))
        else:
            channel.reply(ret)


def raw_rpc():
    return _RawRPCDecorator


def rpc(raises=()):
    return functools.partial(_RPCDecorator, raises=raises)


def event_handler(cls, *args, **kwargs):
    def decorator(func):
        from lymph.core.events import EventHandler
        if isinstance(func, EventHandler):
            raise TypeError('lymph.event() and lymph.task() decorators cannot be stacked')

        def factory(interface):
            return cls(interface, func, *args, **kwargs)
        declaration = Declaration(factory)
        # FIXME(emulbreh): we attach the class here to make TaskHandlers
        # identifyable in the Interface meta class. This isn't pretty and
        # should be cleaned up together with the whole Declaration mess.
        declaration.cls = cls
        return declaration
    return decorator


def event(*event_types, **kwargs):
    from lymph.core.events import EventHandler
    return event_handler(EventHandler, event_types, **kwargs)


def task(sequential=False):
    from lymph.core.events import TaskHandler
    return event_handler(TaskHandler, sequential=sequential)
