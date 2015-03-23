from werkzeug.routing import Rule


class HandledRule(Rule):

    def __init__(self, string, handler, **kwargs):
        self.handler = handler
        super(HandledRule, self).__init__(string, **kwargs)
