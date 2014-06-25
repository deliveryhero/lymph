
Overview
========


Terms
~~~~~

.. glossary::

    service interface
        A collection of rpc methods and event listeners that are exposed by a service container.
        Interfaces are implemented as subclasses of :class:`lymph.Interface`.

    service container
        A service container manages rpc and event connections, service discovery, logging, and configuration
        for one or more service interfaces. There is one container per service instance.

        Containers are :class:`ServiceContainer <lymph.core.container.ServiceContainer>` objects.

    service instance
        A single process that runs a service container.
        It is usually created from the commandline with :ref:`lymph instance <cli-lymph-instance>`.

        Instances are described by :class:`ServiceInstance <lymph.core.services.ServiceInstance>` objects.

    service
        A set of all service instances that exposes a common service interface is called a service.
        Though uncommon, instances may be part of more than one service.

        Services are described by :class:`Service <lymph.core.services.Service>` objects.
