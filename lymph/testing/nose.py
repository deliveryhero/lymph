from __future__ import absolute_import

import logging

from nose.plugins import Plugin

log = logging.getLogger('nose.plugins.lymph')


class LymphPlugin(Plugin):
    """
    Initializes the lymph framework before tests are run
    """

    name = 'lymph'

    def begin(self):
        log.info("Initializing lymph framework")
        import lymph.monkey
        lymph.monkey.patch()
