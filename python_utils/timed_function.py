import signal
import time

class TimedFunction(Exception):
    """
    Its an exception thrown when timeout happens.
    
    # NOTE: this will break in multithreading
    # it should work fine in multiprocessing
    """

    prev = list()

    def __init__(self, timeout=10):
        """
        :param int timeout: timeout in seconds, default 10s
        """
        self._timeout = timeout
        self._started = 0
        self._prev = []

        super(TimedFunction, self).__init__(repr(self))

    def __repr__(self):
        return f'Timeout: {self._timeout} seconds'

    def restore(self, ended=False):
        """ 
        this method restores the original alarm signal handler, or sets up
        the next timer on the pushdown stack.
        """
        if not ended and signal.getitimer(signal.ITIMER_REAL)[0] > 0:
            return
        while self._prev and self in self._prev:
            self._prev.pop()
        if self._prev:
            prev = self._prev[-1]
            time_diff = time.time() - prev.started
            time_remaining = prev.timeout - time_diff
            if time_remaining > 0:
                signal.signal(signal.SIGALRM, prev.fire_timer)
                signal.setitimer(signal.ITIMER_REAL, time_remaining)
            else:
                prev.restore()
        else:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)

    def fire_timer(self, *_sig_param):
        """
        when an itimer fires, execution enters this method
        which either clears timers, sets up the next timer in a nest
        as specified by the options.

        After the timers are handled, this method raises the TimedFunction
        exception.
        """
        self.restore()
        raise self

    def __enter__(self):
        """ 
        the logic that starts the timers is normally fired by the with
        keyword though, with just calls this __enter__ function. The timers
        are started here.
        """
        self._prev.append(self)
        signal.signal(signal.SIGALRM, self.fire_timer)
        self._started = time.time()
        signal.setitimer(signal.ITIMER_REAL, self._timeout)
        return self

    def __exit__(self, e_type, e_obj, e_tb):
        """ 
        when the code leaves the a TimedFunction with block, execution enters this __exit__
        method. It attempts to clean up any remaining timers.
        """
        self.restore(ended=True)


def timedfunction_wrapper(**t_kw):
    """ 
    wrap decroated function in a with TimedFunction block and guard against exceptions
    The options are roughly the same as for TimedFunction with a minor exception.
    options:
    """
    def _decorator(actual):
        def _wrapper(*a, **kw):
            with TimedFunction(**t_kw):
                return actual(*a, **kw)

        return _wrapper

    return _decorator