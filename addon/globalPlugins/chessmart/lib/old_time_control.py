# coding: utf-8


import abc
import typing as t
import math
import re
import dataclasses
import wx
from .helpers import import_bundled


with import_bundled():
    import chess


Seconds = int
RESERVED_TIME = 1
TIME_CONTROL_REGEX = re.compile(
    r"(?P<white_base_time>[0-9]+);(?P<white_increment>[0-9]+);?(?P<black_base_time>[0-9]+)?;?(?P<black_increment>[0-9]+)?"
)
SHORT_TIME_CONTROL_REGEX = re.compile(r"^(?P<base_time>[0-9]+)\+(?P<increment>[0-9]+)$")


@dataclasses.dataclass
class ChessStopWatch:
    base_time: Seconds
    increment: Seconds
    total_time_credit: Seconds = 0
    stopwatch: wx.StopWatch = None
    num_moves: int = 0
    name: str = ""

    def __post_init__(self):
        self.total_time_credit = self.base_time

    def _start_stop_watch(self, starting_value: Seconds = None):
        starting_value = starting_value or self.total_time_credit
        self.stopwatch.Start(starting_value * -1000)

    def start(self):
        if self.stopwatch is None:
            self.stopwatch = wx.StopWatch()
            self._start_stop_watch()
        else:
            raise RuntimeError(f"{self.__class__!r} can only be started once")

    def is_started(self):
        return self.stopwatch is not None

    def get_total(self) -> Seconds:
        return self.base_time + (self.increment * self.num_moves)

    def get_remaining(self) -> Seconds:
        if not self.is_started():
            return self.get_total()
        mils = self.stopwatch.Time()
        if mils >= 0:
            return 0
        return abs(mils // 1000)

    def get_elapsed(self) -> Seconds:
        return self.get_total() - self.get_remaining()

    def pause(self):
        self.stopwatch.Pause()
        current_remaining_time = self.stopwatch.Time() // 1000
        self.total_time_credit = (
            abs(current_remaining_time) + self.increment + RESERVED_TIME
        )

    def resume(self):
        self._start_stop_watch(self.total_time_credit)

    def is_time_up(self):
        return self.get_remaining() <= 0


@dataclasses.dataclass
class ChessTimeControl:
    white_base_time: Seconds
    white_increment: Seconds
    black_base_time: Seconds
    black_increment: Seconds

    def __post_init__(self):
        self.chess_clocks = {
            chess.WHITE: ChessStopWatch(
                base_time=self.white_base_time,
                increment=self.white_increment,
                name="White Clock",
            ),
            chess.BLACK: ChessStopWatch(
                base_time=self.black_base_time,
                increment=self.black_increment,
                name="Black Clock",
            ),
        }

    @classmethod
    def from_string(cls, string_representation: str):
        match = TIME_CONTROL_REGEX.match(string_representation)
        if match is None:
            raise ValueError(
                f"{string_representation} is not a valid string representation of a chess time control"
            )
        kwargs = match.groupdict()
        if kwargs["black_base_time"] is None:
            kwargs["black_base_time"] = kwargs["white_base_time"]
        if kwargs["black_increment"] is None:
            kwargs["black_increment"] = kwargs["white_increment"]
        return cls(**{k: int(v) for k, v in kwargs.items()})

    @classmethod
    def from_time_control_notation(cls, tc):
        parsed = cls.parse_time_control_notation(tc)
        if parsed is None:
            raise ValueError(f"Invalid input time control {tc}")
        base_seconds, increment_seconds = parsed
        return cls(
            white_base_time=base_seconds,
            white_increment=increment_seconds,
            black_base_time=base_seconds,
            black_increment=increment_seconds,
        )

    @staticmethod
    def parse_time_control_notation(tc: str) -> t.Tuple[Seconds, Seconds]:
        match = SHORT_TIME_CONTROL_REGEX.match(tc)
        if match:
            base_min, increment_sec = match.groupdict().values()
            return int(base_min) * 60, int(increment_sec)

    def astuple(self):
        return (
            self.white_base_time,
            self.white_increment,
            self.black_base_time,
            self.black_increment,
        )

    def time_move(self, last_move_maker, total_moves):
        self.chess_clocks[last_move_maker].pause()
        self.chess_clocks[last_move_maker].num_moves += 1
        apponent_clock = self.chess_clocks[not last_move_maker]
        if not apponent_clock.is_started():
            apponent_clock.start()
        else:
            apponent_clock.resume()

    def start_game(self):
        self.chess_clocks[chess.WHITE].start()

    def stop(self):
        self.chess_clocks.clear()

    def get_remaining_time(self) -> tuple:
        return {
            color: self.chess_clocks[color].get_remaining() for color in chess.COLORS
        }

    def is_time_forfeit(self):
        return {color: self.chess_clocks[color].is_time_up() for color in chess.COLORS}


class NullChessTimeControl(ChessTimeControl):
    """Use when time control is not desired."""

    def time_move(self, last_move_maker, total_moves):
        pass

    def start_game(self):
        pass

    def stop(self):
        pass

    def is_time_forfeit(self):
        return {True: False, False: False}


NULL_TIME_CONTROL = NullChessTimeControl(5400, 5400, 30, 30)
