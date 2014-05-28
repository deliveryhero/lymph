import iris


class EchoService(iris.Interface):
    service_type = 'echo'

    @iris.rpc()
    def echo(self, channel, text=None):
        channel.reply(text)

    @iris.rpc()
    def upper(self, channel, text=None):
        channel.reply(text.upper())
        self.emit('uppercase_transform_finished', {'text': text})
