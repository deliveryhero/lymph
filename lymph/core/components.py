import six

from lymph.core.monitoring.metrics import Metrics


class Component(object):
    def __init__(self):
        self.metrics = Metrics()

    def on_start(self):
        pass

    def on_stop(self, **kwargs):
        pass


class Declaration(object):
    def __init__(self, factory):
        self.factory = factory

    def install(self, componentized):
        return componentized.install(self)

    def __call__(self, *args, **kwargs):
        return self.factory(*args, **kwargs)

    def __get__(self, componentized, cls):
        if componentized is None:
            return self
        try:
            return componentized._declared_components[self]
        except KeyError:
            return self.install(componentized)


class ComponentizedBase(type):
    def __new__(cls, clsname, bases, attrs):
        declarations = set()
        for base in bases:
            if isinstance(base, ComponentizedBase):
                declarations.update(base.declarations)
        for name, value in six.iteritems(attrs):
            if isinstance(value, Declaration):
                value.name = name
                declarations.add(value)
        new_cls = super(ComponentizedBase, cls).__new__(cls, clsname, bases, attrs)
        new_cls.declarations = declarations
        return new_cls


@six.add_metaclass(ComponentizedBase)
class Componentized(Component):
    def __init__(self):
        super(Componentized, self).__init__()
        self._declared_components = {}
        self.__all_components = []

    def add_component(self, component):
        self.__all_components.append(component)
        self.metrics.add(component.metrics)

    def install(self, factory, **kwargs):
        if factory in self._declared_components:
            raise RuntimeError("already installed: %s" % factory)
        component = factory(self, **kwargs)
        self._declared_components[factory] = component
        self.add_component(component)
        return component

    def on_start(self):
        for declaration in self.declarations:
            # FIXME: is this the right place to force declaration resolution?
            declaration.__get__(self, type(self))
        for component in self.__all_components:
            component.on_start()

    def on_stop(self, **kwargs):
        for component in reversed(self.__all_components):
            component.on_stop(**kwargs)
