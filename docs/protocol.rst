The Iris RPC Protocol
======================

Message format:

=====  ========  ===========================================================
Index  Name      Content
=====  ========  ===========================================================
0      ID        a random uuid
1      Type      ``REQ``, ``REP``, ``ACK``, ``NACK``, or ``ERROR``
2      Subject   method name for "REQ" messages, else: 
                 message id of the corresponding request
3      Headers   msgpack encoded header dict
4      Body      msgpack encoded body
=====  ========  ===========================================================
    