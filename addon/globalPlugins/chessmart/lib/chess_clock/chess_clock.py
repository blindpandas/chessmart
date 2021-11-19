# coding: utf-8

import time
import enum


Seconds = int

class ClockState(enum.IntFlag):
    NOT_STARTED = enum.auto()
    TICKING = enum.auto()
    PAUSED = enum.auto()
    TIMEOUT = enum.auto()



class ChessClock:

    CLOCK_STATE_LABELS = {
        ClockState.NOT_STARTED: "Not started",
        ClockState.TICKING: "Ticking",
        ClockState.PAUSED: "Paused",
        ClockState.TIMEOUT: "Timeout",
    }

    def __init__(self, base_time: Seconds, increment: Seconds, name=""):
        self.base_time = base_time
        self.increment = increment
        self.name = name
        self.total_time_credit = base_time
        self._remaining = self.total_time_credit
        self.started_at = None
        self.__started_once = False

    def __repr__(self):
        state = self.CLOCK_STATE_LABELS[self.state]
        return f"<ChessClock: state={state}, elapsed={self.elapsed}, remaining={self.remaining}, name={self.name}>"

    @property
    def state(self) -> ClockState:
        if self.__started_once:
            if self.remaining != 0:
                return ClockState.TICKING if self.started_at is not None else ClockState.PAUSED
            return ClockState.TIMEOUT
        else:
            return ClockState.NOT_STARTED

    def _get_elapsed(self):
        return self.total_time_credit - self._get_remaining()

    def _get_remaining(self):
        if not self.__started_once:
            return self.total_time_credit
        elif self.started_at is None:
            remaining = self._remaining
        else:
            remaining = self._remaining - (time.perf_counter() - self.started_at)
        return remaining if remaining >= 0 else 0

    @property
    def elapsed(self):
        return round(self._get_elapsed())

    @property
    def remaining(self):
        return round(self._get_remaining())

    def reset(self, remaining):
        self._remaining = remaining
        if self.state is ClockState.TICKING:
            self.started_at = time.perf_counter()

    def start(self):
        if self.__started_once:
            raise RuntimeError("Clock can only be started once.")
        self.started_at = time.perf_counter()
        self.__started_once = True

    def pause(self, auto_increment):
        if self.state is not ClockState.TICKING:
            raise RuntimeError("Could not pause clock. Clock is not ticking.") 
        inc = self.increment if auto_increment else 0
        self.total_time_credit += inc
        self._remaining += inc
        self._remaining = self._get_remaining()
        self.started_at = None

    def resume(self):
        if self.state is not ClockState.PAUSED:
            raise RuntimeError("Could not resume clock. Clock is not paused.") 
        self.started_at = time.perf_counter()

