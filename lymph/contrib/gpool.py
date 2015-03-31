from gevent.pool import Pool, Group

from lymph.exceptions import ResourceExhausted


class RejectExcecutionError(ResourceExhausted):
    pass


class NonBlockingPool(Pool):
    """A gevent pool that when exhausted will wait for a given timeout
    for resources to be freed before rejecting the job by raising
    exc:``RejectedExcecutionError``.

    When the ``timeout`` is not given or set to None the pool will reject
    immediately without waiting when pool size reach max size.

    In case ``size`` is None this will create an unbound pool.

    """

    def __init__(self, timeout=None, **kwargs):
        super(NonBlockingPool, self).__init__(**kwargs)
        self._timeout = timeout

    def add(self, greenlet):
        acquired = self._semaphore.acquire(blocking=False, timeout=self._timeout)
        # XXX(Mouad): Checking directly for False because DummySemaphore always
        # return None https://github.com/gevent/gevent/pull/544.
        if acquired is False:
            raise RejectExcecutionError('No more resource available to run %r' % greenlet)
        try:
            Group.add(self, greenlet)
        except:
            self._semaphore.release()
            raise
