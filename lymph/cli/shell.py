# -*- coding: utf-8 -*-
import sys
import telnetlib
import logging

from lymph.client import Client
from lymph.cli.base import Command


logger = logging.getLogger(__name__)


class ShellCommand(Command):
    """
    Usage: lymph shell [options]

    Starts an interactive Python shell, locally or remotely

    Options:
      --remote=<name:identity-prefix>     Service instance name and identity.
      --guess-external-ip, -g             Guess the public facing IP of this machine and
                                          use it instead of the provided address.

    {COMMON_OPTIONS}

    Locally:

      In case the shell was open locally the following objects will be
      available in the global namespace:

      ``client``
          a configured :class:`lymph.client.Client` instance

      ``config``
          a loaded :class:`lymph.config.Configuration` instance

    Remotely:

      ``lymph shell --remote=<name>`` can open a remote shell in a running
      service instance, but only if this service is run in ``--debug`` mode.

      In this shell you have access to the current container instance and
      helper functions for debugging purposes:

      ``container``
          the :class:`lymph.core.container.Container` instance

      ``dump_stacks()``
          dumps stack of all running greenlets and os threads

    Example:

        $ lymph shell --remote=echo:38428b071a6 --guess-external-ip
    """

    short_description = 'Starts an interactive Python shell, locally or remotely'

    def run(self, **kwargs):
        self.client = Client.from_config(self.config)

        service_fullname = self.args.get('--remote')
        if service_fullname:
            return self._open_remote_shell(service_fullname)
        else:
            return self._open_local_shell()

    def get_imported_objects(self):
        return {'client': self.client, 'config': self.config}

    def _open_local_shell(self):
        imported_objects = self.get_imported_objects()
        try:
            import IPython
        except ImportError:
            IPython = None

        if IPython:
            IPython.start_ipython(
                argv=[],
                user_ns=imported_objects,
                banner1='Welcome to the lymph shell'
            )
        else:
            import code
            code.interact(local=imported_objects)

    def _open_remote_shell(self, service_fullname):
        backdoor_endpoint = self._get_backdoor_endpoint(service_fullname)
        if not backdoor_endpoint:
            return "No backdoor setup for %s" % service_fullname

        host, port = backdoor_endpoint.split(':')

        self._open_telnet(host, port)

    def _get_backdoor_endpoint(self, service_fullname):
        try:
            name, identity_prefix = service_fullname.split(':')
        except ValueError:
            sys.exit("Malformed argument it should be in the format 'name:identity'")
        service = self.client.container.lookup(name)
        instance = service.get_instance(identity_prefix)
        if instance is None:
            sys.exit('Unkown instance %s' % service_fullname)
        return instance.backdoor_endpoint

    def _open_telnet(self, host, port):
        telnet = telnetlib.Telnet()
        telnet.open(host, port)

        telnet.interact()
