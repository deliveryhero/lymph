Installation
============

In order to use lymph, the following dependencies need to be met:

- Python (2.7, 3.4)
- pip (>=1.5)
- Python headers
- `ZooKeeper`_ (for service discovery)
- `RabbitMQ`_ (for event passing)

If these are already set up, you can skip straight to the installation 
of lymph itself, otherwise proceed with the following steps.


Installing lymph from source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to be able to install the requirements using pip, you need to have the latest
lymph version cloned from the github repository.

.. code:: console

    $ # for Python 2.7
    $ git clone https://github.com/deliveryhero/lymph.git
    $ cd lymph
    $ pip install -r requirements/base2.txt

.. code:: console

    $ # for Python 3.4
    $ git clone https://github.com/deliveryhero/lymph.git
    $ cd lymph
    $ pip install -r requirements/base3.txt


Configuring dependencies
~~~~~~~~~~~~~~~~~~~~~~~~
The RabbitMQ default configuration is usually enough for development and testing.
For detailed information on how to configure ZooKeeper refer to the `ZooKeeper`_
webpage and the `Getting Started Guide`_.


Testing lymph
~~~~~~~~~~~~~

You can test if your installation of lymph has been successful by running the unittests. 
You'll also have to set ``ZOOKEEPER_PATH`` to the directory that contains your ZooKeeper 
binaries (e.g. ``/usr/share/java`` on Ubuntu).

You can then run the tests with either `tox`_ or ``nosetests`` directly.


Installing dependencies on Ubuntu
----------------------------------

.. code:: bash

	$ sudo apt-get install build-essential python-dev python-pip

Install and start zookeeper using:

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
