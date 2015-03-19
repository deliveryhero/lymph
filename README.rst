.. image:: https://travis-ci.org/deliveryhero/lymph.svg?branch=master
    :target: https://travis-ci.org/deliveryhero/lymph


Lymph
=====

lymph is an opinionated framework for Python services. Its features are

* Discovery: pluggable service discovery (e.g. backed by ZooKeeper)
* RPC: request-reply messaging (via ZeroMQ + MessagePack)
* Events: pluggable and reliable pub-sub messaging (e.g. backed by RabbitMQ)
* Process Management

There's `documentation <http://lymph.readthedocs.org/>`_ on readthedocs.org.


Installation (as a dependency)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # py-monotime requires python headers, and gevent and cython require build-essential
    $ sudo apt-get install build-essential python-dev

::

    $ pip install https://github.com/deliveryhero/lymph.git#egg=lymph


Development (of lymph itself)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ git clone https://github.com/deliveryhero/lymph.git
    $ cd lymph
    $ pip install -r requirements/base2.txt -r requirements/dev.txt
    $ pip install -e .

Run tests with ``tox``, build documentation with ``fab docs``.

.. note:: For Python 3
   you need to install cython first
   and use a different requirements file::
    
        $ pip install cython
        $ pip install -r requirements/base3.txt -r requirements/dev.txt


Running services
~~~~~~~~~~~~~~~~

To run the example services, you can use the example node config in 
``conf/sample-node.yml``. You'll also need a local installation
of `ZooKeeper`_ (with the configuration provided in the
`Getting Started Guide`_) and `RabbitMQ`_::

    $ export PYTHONPATH=examples
    $ cp conf/sample-node.yml .lymph.yml
    $ lymph node

You can then discover running services::

    $ lymph discover

and send requests to them from the commandline::

    $ lymph request echo.upper '{"text": "transform me"}'

To see the log output of a running service, try::

    $ lymph tail echo -l DEBUG


.. _ZooKeeper: http://zookeeper.apache.org
.. _Getting Started Guide: http://zookeeper.apache.org/doc/trunk/zookeeperStarted.html
.. _RabbitMQ: http://www.rabbitmq.com/

