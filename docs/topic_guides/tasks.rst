.. _topic-tasks:


Tasks
=====

.. code:: python

    import lymph
    import requests

    class BackgroundPush(lymph.Interface):
        @lymph.task()
        def push_to_3rd_party(self, data):
            requests.post("http://3rd-party.example.com/push", data)

        @lymph.rpc()
        def push(self, data):
            self.push_to_3rd_party.apply(data=data)


Running worker instances:

.. code::

    $ lymph worker -c config.yml

These instances will register as `{interface_name}.worker` and thus not respond 
to RPC requests sent to `{interface_name}`.