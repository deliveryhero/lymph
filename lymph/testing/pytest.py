from __future__ import absolute_import

import logging

log = logging.getLogger(__name__)


def pytest_configure(config):
    log.info("Initializing the lymph framework")
    import lymph.monkey
    lymph.monkey.patch()
