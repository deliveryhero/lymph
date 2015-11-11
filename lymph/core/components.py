import sys
import gevent
import six


class Component(object):
    def __init__(self, error_hook=None, pool=None, metrics=None):
        self._parent_component = None
        self.__error_hook = error_hook
        self.__pool = pool
        self.__metrics = metrics

    def set_parent(self, parent):
        self._parent_component = parent

    def on_start(self):
        pass

    def on_stop(self, **kwargs):
        pass

    @property
    def pool(self):
        if self.__pool is not None:
            return self.__pool
        if not self._parent_component:
            raise TypeError("root component without pool")
        return self._parent_component.pool

    @property
    def error_hook(self):
        if self.__error_hook:
            return self.__error_hook
        if not self._parent_component:
            raise TypeError("root component without error_hook")
        return self._parent_component.error_hook

    @property
    def metrics(self):
        if self.__metrics is not None:
            return self.__metrics
        if not self._parent_component:
            raise TypeError("root component without metrics")
        return self._parent_component.metrics

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
        self._decorators = []

    def __call__(self, *args, **kwargs):
        component = self.factory(*args, **kwargs)
        for decorator in self._decorators:
            component.func = decorator(component.func)
        return component

    def decorate(self, decorator):
        self._decorators.append(decorator)

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
        self.__started = False

    def add_component(self, component):
        component.set_parent(self)
        self.__all_components.append(component)
        if self.__started:
            component.on_start()

    def install(self, factory, **kwargs):
        if factory in self._declared_components:
            raise RuntimeError("already installed: %s" % factory)
        component = factory(self, **kwargs)
        self._declared_components[factory] = component
        self.add_component(component)
        return component

    def on_start(self):
        self.__started = True
        for declaration in self.declarations:
            # FIXME: is this the right place to force declaration resolution?
            declaration.__get__(self, type(self))
        for component in self.__all_components:
            component.on_start()

    def on_stop(self, **kwargs):
        for component in reversed(self.__all_components):
            component.on_stop(**kwargs)
