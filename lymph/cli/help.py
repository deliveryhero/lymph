from lymph.cli.base import Command, get_command_classes, get_command_class, format_docstring


HEADER = 'Usage: lymph [options] <command> [<args>...]'

HELP = HEADER + """
  lymph help             display help overview
  lymph help <command>   display command documentation
"""

TEMPLATE = HEADER + """

{COMMON_OPTIONS}

Commands:
%s
"""


def _format_help(name, description, indent='  ', spaces=13, min_spaces=2):
    r"""Format ``name`` + ``description`` in an unified format
    that can be used to print beautiful help messages.

    If the name is too long (length is greater than ``spaces - min_spaces``)
    than the name and description will appear in different lines.

    Example:

        >>> print(_format_help('foo', 'foobar'))
          foo          foobar
        >>> print(_format_help('foo', 'foobar', spaces=4))
          foo
              foobar
        >>> print('\n'.join([
        ...     _format_help('help', 'Print help message'),
        ...     _format_help('shell', 'Open an interactive Python shell.'),
        ...     _format_help('storage-migration', 'One big name for a command option'),
        ... ]))
        ...
          help         Print help message
          shell        Open an interactive Python shell.
          storage-migration
                       One big name for a command option


    """
    if spaces - len(name) < min_spaces:
        return '\n'.join([
            indent + name,
            indent + (' ' * spaces) + description
        ])
    else:
        return indent + name + (' ' * (spaces - len(name))) + description


class HelpCommand(Command):
    """
    Usage: lymph help [<command>]

    Displays help information about lymph commands
    """

    short_description = 'Displays help information about lymph'
    needs_config = False
    _description = None

    @property
    def description(self):
        if self._description is None:
            classes = get_command_classes()
            cmds = []
            for name, cls in classes.items():
                cmds.append(_format_help(name, cls.short_description))
            self._description = format_docstring(TEMPLATE % '\n'.join(cmds))
            self._description += "\n\nlymph help <command>     to display command specific help"
        return self._description

    def run(self):
        name = self.args['<command>']
        if name:
            print(get_command_class(name).get_help())
        else:
            print(self.description)

