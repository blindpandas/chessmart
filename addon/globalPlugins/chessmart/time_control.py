# coding: utf-8


import abc
import typing as t
import math
import re
import dataclasses
from .helpers import import_bundled


with import_bundled():
    import chess
    from chess_clock import ChessClock, ClockState, Seconds


TIME_CONTROL_REGEX = re.compile(
    r"(?P<white_base_time>[0-9]+);(?P<white_increment>[0-9]+);?(?P<black_base_time>[0-9]+)?;?(?P<black_increment>[0-9]+)?"
)
SHORT_TIME_CONTROL_REGEX = re.compile(r"^(?P<base_time>[0-9]+)\+(?P<increment>[0-9]+)$")


@dataclasses.dataclass
class ChessTimeControl:
    white_base_time: Seconds
    white_increment: Seconds
    black_base_time: Seconds
    black_increment: Seconds

    def __post_init__(self):
        self.chess_clocks = {
            chess.WHITE: ChessClock(
                base_time=self.white_base_time,
                increment=self.white_increment,
                name="White Clock",
            ),
            chess.BLACK: ChessClock(
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
        clock = self.chess_clocks[last_move_maker]
        if clock.state is ClockState.TICKING:
            clock.pause(True)
        apponent_clock = self.chess_clocks[not last_move_maker]
        if apponent_clock.state is ClockState.NOT_STARTED:
            apponent_clock.start()
        else:
            apponent_clock.resume()

    def start_game(self):
        self.chess_clocks[chess.WHITE].start()

    def stop(self):
        self.chess_clocks.clear()

    def get_remaining_time(self) -> tuple:
        return {color: self.chess_clocks[color].remaining for color in chess.COLORS}

    def is_time_forfeit(self):
        return {
            color: self.chess_clocks[color].state is ClockState.TIMEOUT
            for color in chess.COLORS
        }

    def percentage_remaining(self, color: chess.Color):
        clock = self.chess_clocks[color]
        return round(clock.remaining / clock.total_time_credit * 100)


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
