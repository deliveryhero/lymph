import lymph


class EchoService(lymph.Interface):
    service_type = 'echo'

    @lymph.rpc()
    def echo(self, channel, text=None):
        channel.reply(text)

    @lymph.rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())
        self.emit('uppercase_transform_finished', {'text': text})
