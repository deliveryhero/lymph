from __future__ import absolute_import

import logging

from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.iris')


class IrisPlugin(Plugin):
    """
    Initializes the iris framework before tests are run
    """

    name = 'iris'

    def begin(self):
        log.info("Initializing iris framework")
        import iris.monkey
        iris.monkey.patch()
