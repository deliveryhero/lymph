Service Discovery
=================

Overview
~~~~~~~~

Lymph provides a distributed service discovery mechanism. Lymph services
are registered with the service registry and are then immediately discoverable
from within any other service.

Lymph uses ZooKeeper to manage, distribute, and sync the services across 
multiple nodes. ZooKeeper is a centralized service for managing configuration
across multiple distributed nodes. It is structured like a "file system",
providing hierarchical namespace. Each entry is specified by a path, which
like in a file system has directories and "files" (which are called znodes).
ZooKeeper replicates and synchronizes these znodes over the whole ZK cluster.

The discovery service can be set in the :file:`.lymph.yml` configuration file:

.. code:: yaml

    registry:
        class: lymph.discovery.zookeeper:ZookeeperServiceRegistry
        hosts: 127.0.0.1:2181

See :ref:`registry-config` for details.


Command line interface
~~~~~~~~~~~~~~~~~~~~~~

To interact with the service discovery system from the command line, you can use the :ref:`discover <cli-lymph-discover>` command.
It displays a list of registered services and service instances:

.. code:: bash

	$ lymph discover
	demo [1]
	echo [1]
	$ lymph discover --instances
	demo [1]
	└─ [cd7c7dae1c] tcp://127.0.0.1:52073
	echo [1]
	└─ [8d8235923e] tcp://127.0.0.1:52822

The information you get per instance is the instance id and its corresponding
ZeroMQ endpoint.


Implementation Details
~~~~~~~~~~~~~~~~~~~~~~

Structure
^^^^^^^^^

Lymph stores all its information under the ``/lymph`` root. This behavior can
be altered in ``lymph/discovery/zookeeper.py``. Below, all paths will
be in relation to this root node (``/`` is actually ``/lymph/``).

Services are registered under ``/services`` and for each service type, a new
directory is created below. In the Lymph source, we call services "service types".
Each service type can then have multiple instances running on the clusters. These
instances are called "identities" in the code. (For a list of terminology, please
refer to :doc:`../getting_started`)

Then for each service type, all its identities are saved below each service type
path.

The complete directory structure is thus:

.. code::

	/lymph/INTERFACE_NAME/IDENTITY

The identity znode holds information about its

- endpoint
- identity
- log_endpoint

