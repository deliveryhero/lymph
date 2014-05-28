.. image:: https://travis-ci.org/deliveryhero/iris.svg?branch=master
    :target: https://travis-ci.org/deliveryhero/iris


Iris
====

iris is an opinionated framework for Python services. Its features are

* Discovery: pluggable service discovery (e.g. backed by ZooKeeper)
* RPC: request-reply messaging (via ZeroMQ + MessagePack)
* Events: pluggable and reliable pub-sub messaging (e.g. backed by RabbitMQ)
* Process Management

There's `documentation <http://iris.readthedocs.org/>`_ on readthedocs.org.


Installation (as a dependency)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # py-monotime requires python headers, and gevent and cython require build-essential
    $ sudo apt-get install build-essential python-dev

::

    $ pip install http://py-monotime.googlecode.com/archive/5fb3eb35a8e25140204e957bd010991bfe8758e3.zip#egg=monotime
    $ pip install https://github.com/johbo/gevent/archive/1.1-dev-20140506.tar.gz#egg=gevent-1.1-dev-20140506
    $ pip install https://github.com/deliveryhero/iris.git#egg=iris


Development (of iris itself)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ git clone https://github.com/deliveryhero/iris.git
    $ cd iris
    $ pip install cython
    $ pip install -r requirements/base.txt -r requirements/dev.txt
    $ pip install -e .

Run tests with ``tox``, build documentation with ``fab docs``.


Running services
~~~~~~~~~~~~~~~~

To run the example services, you can use the example node config in 
``conf/local-zookeeper-rabbitmq-node.yml``. You'll also need a local installation
of `ZooKeeper`_ (with the configuration provided in the
`Getting Started Guide`_) and `RabbitMQ`_::

    $ export PYTHONPATH=examples
    $ cp conf/local-zookeeper-rabbitmq-node.yml .iris.yml
    $ iris node

You can then discover running services::

    $ iris discover

and send requests to them from the commandline::

    $ iris request iris://echo echo.upper '{"text": "transform me"}'

To see the log output of a running service, try::

    $ iris tail iris://echo -l DEBUG


.. _ZooKeeper: http://zookeeper.apache.org
.. _Getting Started Guide: http://zookeeper.apache.org/doc/trunk/zookeeperStarted.html
.. _RabbitMQ: http://www.rabbitmq.com/

