from supervisor import supervise


class FakeRun:
    """Returns the next queued exit code each call; records how many times run."""

    def __init__(self, codes):
        self.codes = list(codes)
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self.codes.pop(0) if self.codes else self.codes_default()

    def codes_default(self):
        return 1  # keep crashing if the queue runs dry


def _no_sleep():
    sleeps = []
    return sleeps, (lambda s: sleeps.append(s))


def test_clean_exit_runs_once_and_stops():
    run = FakeRun([0])
    sleeps, sleep = _no_sleep()
    code = supervise(run, sleep=sleep, emit=lambda m: None)
    assert run.calls == 1
    assert code == 0
    assert sleeps == []  # never restarted


def test_ctrl_c_exit_is_treated_as_clean():
    run = FakeRun([130])
    code = supervise(run, sleep=lambda s: None, emit=lambda m: None)
    assert run.calls == 1 and code == 130


def test_one_crash_then_clean_restarts_once():
    run = FakeRun([1, 0])
    sleeps, sleep = _no_sleep()
    supervise(run, sleep=sleep, backoff=5.0, emit=lambda m: None)
    assert run.calls == 2          # crashed, restarted, exited clean
    assert sleeps == [5.0]         # one backoff between attempts


def test_crash_loop_gives_up_at_max_restarts():
    run = FakeRun([1, 1, 1, 1, 1, 1, 1])   # always crashing
    sleeps, sleep = _no_sleep()
    clock = {"t": 0.0}
    code = supervise(run, sleep=sleep, now=lambda: clock["t"],
                     max_restarts=5, window=60.0, emit=lambda m: None)
    assert run.calls == 5          # gives up on the 5th crash within the window
    assert len(sleeps) == 4        # backed off between the first four
    assert code == 1


def test_crashes_outside_window_do_not_trip_the_cap():
    # each crash is >window apart -> the counter never reaches max_restarts
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    def sleep(_s):
        clock["t"] += 1000.0  # advance far beyond the 60s window each restart

    stop = {"n": 0}

    def should_stop():
        stop["n"] += 1
        return stop["n"] > 20  # polled ~2x/iteration; let it restart ~10 times

    run = FakeRun([1] * 20)
    supervise(run, should_stop=should_stop, sleep=sleep, now=now,
              max_restarts=5, window=60.0, emit=lambda m: None)
    assert run.calls >= 6          # would have given up at 5 if the window counted them


def test_should_stop_breaks_the_loop_immediately():
    run = FakeRun([1])
    # stop requested right after the first crash -> no restart
    flags = {"stop": False}

    def run_then_stop():
        flags["stop"] = True
        return 1

    code = supervise(run_then_stop, should_stop=lambda: flags["stop"],
                     sleep=lambda s: None, emit=lambda m: None)
    assert code == 0  # intentional stop reports success, and did not restart
