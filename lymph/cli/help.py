from lymph.cli.base import Command, get_command_classes, get_command_class, format_docstring


HELP = 'Usage: lymph [options] <command> [<args>...]'

TEMPLATE = HELP + """

{COMMON_OPTIONS}

Commands:
%s
"""


def _format_help(name, description, space=13, min_space=2):
    r"""Format ``name`` + ``description`` in an unified format
    that can be used to print beautiful help messages.

    If the name is too long (length is greater than ``space - min_space``
    than the name and description will appear in different lines.

    Example:

        >>> print(format_help('foo', 'foobar'))
        foo          foobar
        >>> print(format_help('foo', 'foobar', space=4))
        foo
            foobar
        >>> print('\n'.join([
        ...     format_help('help', 'Print help message'),
        ...     format_help('shell', 'Open an interactive Python shell.')
        ... ]))
        ...
        help         Print help message
        shell        Open an interactive Python shell.


    """
    if space - len(name) < min_space:
        return '\n'.join([
            name, (' ' * space) + description
        ])
    else:
        return name + (' ' * (space - len(name))) + description


class HelpCommand(Command):
    """
    Usage: lymph help [<command>]
    """

    short_description = 'Display help information about lymph.'
    needs_config = False
    _description = None

    @property
    def description(self):
        if self._description is None:
            classes = get_command_classes()
            cmds = []
            for name, cls in classes.items():
                cmds.append('  ' + _format_help(name, cls.short_description))
            self._description = format_docstring(TEMPLATE % '\n'.join(cmds))
        return self._description

    def run(self):
        name = self.args['<command>']
        if name:
            print(get_command_class(name).get_help())
        else:
            print(self.description)

