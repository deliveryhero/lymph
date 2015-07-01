import six


class RpcError(Exception):
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self)


class RpcRequestError(RpcError):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(RpcError, self).__init__(*args, **kwargs)


class Timeout(RpcRequestError):
    pass


class Nack(RpcRequestError):
    pass


class LookupFailure(RpcError):
    pass


class RegistrationFailure(RpcError):
    pass


class EventHandlerTimeout(Exception):
    pass


class _RemoteException(type):

    # Hold dynamically generated exception classes.
    __exclasses = {}

    def __getattr__(cls, errtype):
        return cls.__exclasses.setdefault(errtype, type(errtype, (cls,), {}))


@six.add_metaclass(_RemoteException)
class RemoteError(RpcRequestError):
    @classmethod
    def from_reply(cls, request, reply):
        errtype = reply.body.get('type', cls.__name__)
        subcls = getattr(cls, errtype)
        return subcls(request, reply.body.get('message', ''))


class SocketNotCreated(Exception):
    pass


class NoSharedSockets(Exception):
    pass


class NotConnected(Exception):
    pass


class ResourceExhausted(Exception):
    pass


class ConfigurationError(Exception):
    pass
