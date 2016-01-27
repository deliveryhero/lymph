from __future__ import absolute_import

import logging

from nose2.events import Plugin


log = logging.getLogger('nose2.plugins.lymph')


class LymphPlugin(Plugin):
    """
    Initializes the lymph framework before tests are run
    """
    configSection = 'lymph'

    def createTests(self, event):
        log.info("Initializing lymph framework")
        import lymph.monkey
        lymph.monkey.patch()
