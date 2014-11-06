import lymph


class EchoService(lymph.Interface):
    service_type = 'echo'

    @lymph.rpc()
    def echo(self, text=None):
        return text

    @lymph.rpc()
    def upper(self, text=None):
        self.emit('uppercase_transform_finished', {'text': text})
        return text.upper()
