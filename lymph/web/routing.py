from werkzeug.routing import Rule


class HandledRule(Rule):

    def __init__(self, string, handler, **kwargs):
        self.handler = handler
        super(HandledRule, self).__init__(string, **kwargs)

    def get_empty_kwargs(self):
        empty_kwargs = super(HandledRule, self).get_empty_kwargs()
        empty_kwargs['handler'] = self.handler
        return empty_kwargs

