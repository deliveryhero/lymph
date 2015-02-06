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
    
        Creates an instance of the class given by a fully qualified name in
        ``self.get(key, default_class)`` by calling a 
        ``from_config()`` classmethod. The ``config`` argument
        will be a :class:`ConfigView` of ``self[key]``.
        
        Given a config file like the following:
        
        .. code-block:: yaml

            foo:
                class: pack.age:SomeClass
                extra_arg: 42


        You can create an instance of SomeClass

        .. code-block:: python

            # in pack/age.py
            class SomeClass(object):
                @classmethod
                def from_config(cls, config, **kwargs):
                    assert config['extra_arg'] == 42
                    assert kwargs['bar'] is True
                    return cls(...)

            config = Configuration()
            config.load(...)
            config.create_instance('foo', bar=True)
    
    .. method:: get_instance(key, default_class, **kwargs)
        
        Like ``create_instance()``, but only creates a single instance for each 
        key.
            

