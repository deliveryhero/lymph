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
            print(u'{t.bold}{name:<15}{t.normal}{description}'.format(
                t=self.terminal,
                name=name,
                description=cls.short_description
            ))

