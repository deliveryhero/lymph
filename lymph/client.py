from lymph.core.container import create_container
from lymph.core.interfaces import Interface


class ClientInterface(Interface):
    def should_register(self):
        return False


class Client(object):
    def __init__(self, container, interface=ClientInterface):
        self.container = container
        self.interface = container.install_interface(interface, name='_client')

    @classmethod
    def from_config(cls, config, **kwargs):
        interface_cls = kwargs.pop('interface_cls', ClientInterface)
        container = create_container(config)
        client = cls(container, interface_cls)
        container.start(register=False)
        return client

    def __getattr__(self, name):
        # FIXME: explicit is better than implicit
        return getattr(self.interface, name)


