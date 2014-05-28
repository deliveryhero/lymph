
class RpcError(Exception):
    def __init__(self, msg, *args, **kwargs):
        self.message = msg
        super(RpcError, self).__init__(*args, **kwargs)


class Timeout(RpcError):
    pass


class Nack(RpcError):
    pass


class LookupFailure(RpcError):
    pass


class RegistrationFailure(Exception):
    pass


class ErrorReply(RpcError):
    def __init__(self, request, reply, *args, **kwargs):
        self.reply = reply
        super(ErrorReply, self).__init__(request, *args, **kwargs)
