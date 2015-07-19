Installation
============

Installing lymph itself (for Python 2.7 or 3.4) is as simple as

.. code:: bash

    $ pip install lymph

but in order to make full use of lymph you'll also need to install 
`ZooKeeper`_ (for service discovery) and `RabbitMQ`_ (for events).

If these are already set up, you can skip straight to 
:ref:`writing your first service <getting-started>`, otherwise proceed with the 
following steps.


Configuring dependencies
~~~~~~~~~~~~~~~~~~~~~~~~
The RabbitMQ default configuration is usually enough for development and testing.
For detailed information on how to configure ZooKeeper refer to the `ZooKeeper`_
webpage and the `Getting Started Guide`_.


Testing lymph
~~~~~~~~~~~~~

.. FIXME move this somewhere else

You can test if your installation of lymph has been successful by running the unittests. 
You'll also have to set ``ZOOKEEPER_PATH`` to the directory that contains your ZooKeeper 
binaries (e.g. ``/usr/share/java`` on Ubuntu).

You can then run the tests with either `tox`_ or ``nosetests`` directly.


Installing dependencies on Ubuntu
----------------------------------

.. code:: bash

	$ sudo apt-get install build-essential python-dev python-pip

Install and start ZooKeeper using:

.. code:: bash

	$ sudo apt-get install zookeeper zookeeperd
	$ sudo service zookeeper start
    
You can edit the config file at ``/etc/zookeeper/conf/zoo.cfg``.

Install and start RabbitMQ:

.. code:: bash

    $ sudo apt-get install rabbitmq-server
    $ service rabbitmq-server start


Installing dependencies on Mac OS X
------------------------------------

.. code:: bash

    $ brew install zookeeper

You can edit the config file at ``/usr/local/etc/zookeeper/zoo.cfg``.


.. _ZooKeeper: http://zookeeper.apache.org
.. _RabbitMQ: http://www.rabbitmq.com/
.. _Getting Started Guide: http://zookeeper.apache.org/doc/trunk/zookeeperStarted.html
.. _tox: https://testrun.org/tox/latest/
