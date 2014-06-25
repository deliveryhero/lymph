from __future__ import absolute_import

import logging
import pdb
import six
import socket
import sys


logger = logging.getLogger(__name__)


class Ripdb(pdb.Pdb):
    """
    Based on
        * https://github.com/tamentis/rpdb
        * http://blog.ionelmc.ro/2013/06/05/python-debugging-tools/

    """
    def __init__(self, port=0):
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.bind(('0.0.0.0', port))
        if not port:
            logger.critical("PDB remote session open on: %s", self.listen_socket.getsockname())
            six.print_("PDB remote session open on:", self.listen_socket.getsockname(), file=sys.__stderr__)
            sys.stderr.flush()
        self.listen_socket.listen(1)
        self.connected_socket, address = self.listen_socket.accept()
        self.handle = self.connected_socket.makefile('rw')
        pdb.Pdb.__init__(self, stdin=self.handle, stdout=self.handle)
        sys.stdout = sys.stdin = self.handle

    def do_continue(self, arg):
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        self.handle.close()
        self.connected_socket.close()
        self.listen_socket.close()
        self.set_continue()
        return 1

    do_c = do_cont = do_continue


def set_trace():
    Ripdb().set_trace(sys._getframe().f_back)
