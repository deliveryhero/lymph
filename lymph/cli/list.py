import six

from lymph.cli.base import Command, get_command_classes


class ListCommand(Command):
    """
    Usage: lymph list [options]

    {COMMON_OPTIONS}
    """

    short_description = 'List available commands.'
    needs_config = False

    def run(self):
        for name, cls in six.iteritems(get_command_classes()):
            print(u'%-15s   %s' % (name, cls.short_description))

