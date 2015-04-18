.. currentmodule:: lymph.config


Config API
==========

.. class:: ConfigView(config, prefix)
    
    A ConfigView allows access to a subtree of a :class:`Configuration` object.
    It implements the mapping protocol. Dotted path keys are translated into
    nested dictionary lookups, i.e. ``cv.get('a.b')`` is (roughly) equivalent to 
    ``cv.get('a').get('b')``.
    
    If a value returned by :class:`ConfigView` methods is a dict, it will be 
    wrapped in a :class:`ConfigView` itself. This – and getting dicts from a 
    :class:`Configuration` object – are the preferred way to create new ConfigViews.
    

    .. attribute:: root
    
        A reference to the root :class:`Configuration` instance.


.. class:: Configuration(values=None)

    :param values: an optional initial mapping

    Configuration implements the same interface as :class:`ConfigView` in addition
    to the methods described here.
    
    .. method:: load(file, sections=None)
    
        Reads yaml configuration from a file-like object. If sections is not 
        None, only the keys given are imported
    
    .. method:: load_file(path, sections=None)
    
        Reads yaml configuration from the file at ``path``.

    .. method:: get_raw(key, default)
    
        Like ``get()``, but doesn't wrap dict values in :class:`ConfigView`.
    
    .. method:: create_instance(key, default_class=None, **kwargs)

        :param key: dotted config path (e.g. ``"container.rpc"``)
        :param default_class: class object or fully qualified name of a class
        :param kwargs: extra keyword arguments to be passed to the factory

        Creates an object from the config dict at ``key``. The instance is
        created by a factory that is specified by its fully qualified name in
        a ``class`` key of the config dict.
        
        If the factory has a ``from_config()`` method it is called with a :class:`ConfigView`
        of ``key``. Otherwise, the factory is called directly with the config values as keyword arguments.
        
        Extra keyword arguments to ``create_instance()`` are passed through to ``from_config()`` or mixed
        into the arguments if the factory is a plain callable.

        If the config doesn't have a ``class`` key the instance is create by ``default_class``, which can be
        either a fully qualifed name or a factory object.

        Given the following config file

        .. code-block:: yaml

            foo:
                class: pack.age:SomeClass
                extra_arg: 42


        you can create an instance of SomeClass

        .. code-block:: python

            # in pack/age.py
            class SomeClass(object):
                @classmethod
                def from_config(cls, config, **kwargs):
                    assert config['extra_arg'] == 42
                    assert kwargs['bar'] is True
                    return cls(...)

            # in any module
            config = Configuration()
            config.load(...)
            config.create_instance('foo', bar=True)
    
    .. method:: get_instance(key, default_class, **kwargs)
        
        Like ``create_instance()``, but only creates a single instance for each 
        key.
            

