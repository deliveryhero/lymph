
def setup_config(args):
    import os
    import sys

    from lymph.config import Configuration
    from lymph.utils.sockets import guess_external_ip

    vars_file = args.get('--vars') or os.environ.get('LYMPH_VARS')
    env_vars = Configuration(raw=True)
    if vars_file:
        env_vars.load_file(vars_file)
        os.environ['LYMPH_VARS'] = vars_file

    config = Configuration({'container': {}}, env=os.environ, var=env_vars)

    if 'LYMPH_NODE_CONFIG' in os.environ:
        config.load_file(os.environ['LYMPH_NODE_CONFIG'], sections=['container', 'registry', 'event_system', 'plugins', 'dependencies'])

    config_file = args.get('--config') or os.environ.get('LYMPH_CONFIG', '.lymph.yml')
    config.load_file(config_file)
    config.source = config_file

    config.setdefault('container.ip', os.environ.get('LYMPH_NODE_IP', '127.0.0.1'))
    ip = args.get('--ip')
    if args.get('--guess-external-ip'):
        if ip:
            sys.exit('Cannot combine --ip and --guess-external-ip')
        ip = guess_external_ip()
        if ip is None:
            sys.exit('Cannot guess external ip, aborting ...')
    if ip:
        config.set('container.ip', ip)

    port = args.get('--port')
    if port:
        config.set('container.port', port)

    return config


def setup_terminal(args, config):
    import blessings

    force_color = args.get('--color', False)
    if args.get('--no-color', False):
        if force_color:
            raise ValueError("cannot combine --color and --no-color")
        force_color = None
    return blessings.Terminal(force_styling=force_color)


def _excepthook(type, value, tb):
    import logging

    logger = logging.getLogger('lymph')
    logger.log(logging.CRITICAL, 'Uncaught exception', exc_info=(type, value, tb))


def main(argv=None):
    import lymph.monkey
    lymph.monkey.patch()

    import docopt
    import sys
    import logging

    from lymph import __version__ as VERSION
    from lymph.cli.help import HELP
    from lymph.cli.base import get_command_class
    from lymph.utils import logging as lymph_logging

    args = docopt.docopt(HELP, argv, version=VERSION, options_first=True)
    name = args.pop('<command>')
    argv = args.pop('<args>')
    try:
        command_cls = get_command_class(name)
    except KeyError:
        print("'%s' is not a valid lymph command. See 'lymph list' or 'lymph help'." % name)
        return 1
    command_args = docopt.docopt(command_cls.get_help(), [name] + argv)
    args.update(command_args)

    config = setup_config(args) if command_cls.needs_config else None

    if config:
        loglevel = args.get('--loglevel', 'ERROR')
        logfile = args.get('--logfile')

        lymph_logging.setup_logging(config, loglevel, logfile)
    else:
        logging.basicConfig()

    sys.excepthook = _excepthook

    terminal = setup_terminal(args, config)
    command = command_cls(args, config, terminal)
    return command.run()


if __name__ == '__main__':
    main()
