import sys
import gevent
import six


class Component(object):
    def __init__(self, error_hook=None, pool=None):
        self._parent_component = None
        self.__error_hook = error_hook
        self.__pool = pool

    def on_start(self):
        pass

    def on_stop(self, **kwargs):
        pass

    def _get_metrics(self):
        return []

    @property
    def pool(self):
        if self.__pool is not None:
            return self.__pool
        if not self._parent_component:
            raise AttributeError("root component without pool")
        return self._parent_component.pool

    @property
    def error_hook(self):
        if self.__error_hook:
            return self.__error_hook
        if not self._parent_component:
            raise AttributeError("root component without error_hook")
        return self._parent_component.error_hook

    def spawn(self, func, *args, **kwargs):
        def _inner():
            try:
                return func(*args, **kwargs)
            except gevent.GreenletExit:
                raise
            except:
                self.error_hook(sys.exc_info())
                raise
        return self.pool.spawn(_inner)


class Declaration(object):
    def __init__(self, factory):
        self.factory = factory

    def __call__(self, *args, **kwargs):
        return self.factory(*args, **kwargs)

    def __get__(self, componentized, cls):
        if componentized is None:
            return self
        try:
            return componentized._declared_components[self]
        except KeyError:
            return componentized.install(self)


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
    def __init__(self, **kwargs):
        super(Componentized, self).__init__(**kwargs)
        self._declared_components = {}
        self.__all_components = []

    def add_component(self, component):
        component._parent_component = self
        self.__all_components.append(component)

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

    def _get_metrics(self):
        for metric in super(Componentized, self)._get_metrics():
            yield metric
        for component in self.__all_components:
            for metric in component._get_metrics():
                yield metric
