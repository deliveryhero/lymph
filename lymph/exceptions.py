import six


class RpcError(Exception):
    def __init__(self, msg, *args, **kwargs):
        self.message = msg or ''
        super(RpcError, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.message

    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__, self)


class Timeout(RpcError):
    pass


class Nack(RpcError):
    pass


class LookupFailure(RpcError):
    pass


class RegistrationFailure(Exception):
    pass


class EventHandlerTimeout(Exception):
    pass


class _RemoteException(type):

    # Hold dynamically generated exception classes.
    __exclasses = {}

    def __getattr__(cls, errtype):
        return cls.__exclasses.setdefault(errtype, type(errtype, (cls,), {}))


@six.add_metaclass(_RemoteException)
class RemoteError(RpcError):

    def __init__(self, request, message):
        self.request = request
        super(RemoteError, self).__init__(message)

    @classmethod
    def from_reply(cls, request, reply):
        errtype = reply.body.get('type', cls.__name__)
        subcls = getattr(cls, errtype)
        return subcls(request, reply.body.get('message', ''))


class SocketNotCreated(Exception):
    pass


class NotConnected(Exception):
    pass
