import blessings


zmqpub_log_handler = None


def _get_zmqpub_log_handler(**kwargs):
    # This function is used by the logging dictConfig to expose the ZeroMQ log
    # handler singleton (``(): lymph.cli.main._get_zmqpub_log_handler``).
    return zmqpub_log_handler


def setup_logging(args, config):
    print(args)
    import logging
    from logging.config import dictConfig
    from lymph.utils.logging import PubLogHandler

    if config is None:
        logging.basicConfig()
        return

    global zmqpub_log_handler
    zmqpub_log_handler = PubLogHandler(config.get('container.log_endpoint', 'tcp://%s' % config.get('container.ip')))

    logconf = dict(config.get('logging', {}))
    logconf.setdefault('version', 1)
    formatters = logconf.setdefault('formatters', {})
    formatters.setdefault('_trace', {
        '()': 'lymph.core.trace.TraceFormatter',
        'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s - (trace-id:%(trace_id)s)',
    })
    handlers = logconf.setdefault('handlers', {})
    handlers.setdefault('_zmqpub', {
        '()': 'lymph.cli.main._get_zmqpub_log_handler',
        'formatter': '_trace',
    })
    console_logconf = {
        'class': 'logging.StreamHandler',
        'formatter': '_trace',
        'level': args['--loglevel'].upper(),
    }
    logfile = args['--logfile']
    if logfile:
        console_logconf.update({
            'class': 'logging.FileHandler',
            'filename': logfile
        })
    handlers.setdefault('_console', console_logconf)
    loggers = logconf.setdefault('loggers', {})
    loggers.setdefault('lymph', {
        'handlers': ['_console', '_zmqpub'],
        'level': 'DEBUG',
    })
    loggers.setdefault('kazoo', {
        'handlers': ['_console', '_zmqpub'],
        'level': 'INFO',
    })
    dictConfig(logconf)


def setup_config(args):
    import os

    from lymph.config import Configuration
    from lymph.utils.sockets import guess_external_ip

    config = Configuration({
        'container': {}
    })

    if 'LYMPH_NODE_CONFIG' in os.environ:
        config.load_file(os.environ['LYMPH_NODE_CONFIG'], sections=['registry', 'event_system', 'plugins'])

    config_file = args.get('--config') or '.lymph.yml'
    config.load_file(config_file)
    config.source = config_file

    config.setdefault('container.ip', os.environ.get('LYMPH_NODE_IP', '127.0.0.1'))
    ip = args.get('--ip')
    if args.get('--guess-external-ip'):
        if ip:
            print('cannot combine --ip and --guess-external-ip')
            return 1
        ip = guess_external_ip()
    if ip:
        config.set('container.ip', ip)

    port = args.get('--port')
    if port:
        config.set('container.port', port)

    return config


def setup_terminal(args, config):
    force_color = args.get('--color', False)
    if args.get('--no-color', False):
        if force_color:
            raise ValueError("cannot combine --color and --no-color")
        force_color = None
    return blessings.Terminal(force_styling=force_color)


def main(argv=None):
    import lymph.monkey
    lymph.monkey.patch()

    import docopt

    from lymph import __version__ as VERSION
    from lymph.cli.help import HELP
    from lymph.cli.base import get_command_class

    args = docopt.docopt(HELP, argv, version=VERSION, options_first=True)
    name = args.pop('<command>')
    argv = args.pop('<args>')
    try:
        command_cls = get_command_class(name)
    except KeyError:
        print("'%s' is not a valid lymph command. See 'lymph list' or 'lymph --help'." % name)
        return 1
    command_args = docopt.docopt(command_cls.get_help(), [name] + argv)
    args.update(command_args)

    config = setup_config(args) if command_cls.needs_config else None

    setup_logging(args, config)
    if config:
        config.set('container.log_endpoint', zmqpub_log_handler.endpoint)
    terminal = setup_terminal(args, config)
    command = command_cls(args, config, terminal)
    return command.run()
