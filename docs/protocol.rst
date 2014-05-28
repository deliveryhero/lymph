The Iris RPC Protocol
======================

Message format:

=====  ========  ===========================================================
Index  Name      Content
=====  ========  ===========================================================
0      ID        a random uuid
1      Type      ``REQ``, ``REP``, or ``ACK``
2      Subject   method name for "REQ" messages, else: 
                 message id of the corresponding request
3      Body      msgpack encoded bytestring
=====  ========  ===========================================================
    