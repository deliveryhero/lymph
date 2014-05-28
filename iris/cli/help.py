from iris.cli.base import Command, format_docstring, get_command_class


HELP = format_docstring("""
Usage: iris [options] <command> [<args>...]

Iris is the personification of the rainbow and messenger of the gods.

{COMMON_OPTIONS}

Commands:
  instance   Run a single service instance (one process).
  node       Run a node service that manages a group of processes on the same
             machine.
  request    Send a request message to some service and output the reply.
  inspect    Describe the available rpc methods of a service.
  tail       Stream the logs of one or more services.
  discover   Show available services.
  help       Display help information about iris.

""")


class HelpCommand(Command):
    """
    Usage: iris help [<command>]
    """

    short_description = 'Display help information about iris.'
    needs_config = False

    def run(self):
        name = self.args['<command>']
        if name:
            print(get_command_class(name).get_help())
        else:
            print(HELP)
