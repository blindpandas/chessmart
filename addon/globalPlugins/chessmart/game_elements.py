# coding: utf-8

import typing
import dataclasses
import random
from utils.displayString import DisplayStringIntEnum
from .virtual_chessboard import BaseVirtualChessboard
from .helpers import import_bundled
from .time_control import NULL_TIME_CONTROL, ChessTimeControl


with import_bundled():
    import chess
    import chess.variant
    from cached_property import cached_property


@dataclasses.dataclass
class GameInfo:
    pychess_board: chess.BaseBoard
    variant: typing.ForwardRef("ChessVariant")
    time_control: ChessTimeControl
    prospective: chess.Color
    custom_starting_fen: str = None
    vboard_kwargs: dict = dataclasses.field(default_factory=dict)

    def asdict(self):
        return dict(
            chessboard_class=self.chessboard_class,
            pychess_board=self.pychess_board,
            time_control=self.time_control,
            prospective=self.prospective,
            use_visuals=self.use_visuals,
            vboard_kwargs=self.vboard_kwargs,
        )


class PlayMode(DisplayStringIntEnum):
    HUMAN_VERSUS_COMPUTER = 0
    HUMAN_VERSUS_HUMAN = 1
    ONLINE_LICHESS_ORG = 2

    @cached_property
    def _displayStringLabels(self):
        return {
            PlayMode.HUMAN_VERSUS_HUMAN: _("Human versus human"),
            PlayMode.HUMAN_VERSUS_COMPUTER: _("Human versus computer"),
            PlayMode.ONLINE_LICHESS_ORG: _("Online (lichess.org)"),
        }

    def get_board_class(self):
        from .virtual_chessboard import (
            UserUserChessboard,
            UserEngineChessboard,
            InternetChessboard,
        )
        if self is PlayMode.HUMAN_VERSUS_HUMAN:
            return UserUserChessboard
        elif self is PlayMode.HUMAN_VERSUS_COMPUTER:
            return UserEngineChessboard
        elif self is PlayMode.ONLINE_LICHESS_ORG:
            return InternetChessboard


class TimeControl(DisplayStringIntEnum):
    CLASSICAL = 0
    RAPID_PLAY_1 = 1
    RAPID_PLAY_2 = 2
    BLITZ_1 = 3
    BLITZ_2 = 4
    BULLET_1 = 5
    BULLET_2 = 6
    CUSTOM = 7
    NUL_TIME_CONTROL = 8

    @cached_property
    def _displayStringLabels(self):
        return {
            TimeControl.NUL_TIME_CONTROL: _("No Time Control"),
            TimeControl.CLASSICAL: _("Classical  (90+30)"),
            TimeControl.RAPID_PLAY_1: _("Rapid Play (15+10)"),
            TimeControl.RAPID_PLAY_2: _("Rapid Play (10+5)"),
            TimeControl.BLITZ_1: _("Blitz (5+5)"),
            TimeControl.BLITZ_2: _("Blitz (3+2)"),
            TimeControl.BULLET_1: _("Bullet (2+2)"),
            TimeControl.BULLET_2: _("Bullet (1+0)"),
            TimeControl.CUSTOM: _("Custom Time Control"),
        }

    def get_time_control(self):
        if self is TimeControl.NUL_TIME_CONTROL:
            return NULL_TIME_CONTROL
        elif self is TimeControl.CLASSICAL:
            return ChessTimeControl.from_time_control_notation("90+30")
        elif self is TimeControl.RAPID_PLAY_1:
            return ChessTimeControl.from_time_control_notation("15+10")
        elif self is TimeControl.RAPID_PLAY_2:
            return ChessTimeControl.from_time_control_notation("10+5")
        elif self is TimeControl.BLITZ_1:
            return ChessTimeControl.from_time_control_notation("5+5")
        elif self is TimeControl.BLITZ_2:
            return ChessTimeControl.from_time_control_notation("3+2")
        elif self is TimeControl.BULLET_1:
            return ChessTimeControl.from_time_control_notation("2+2")
        elif self is TimeControl.BULLET_2:
            return ChessTimeControl.from_time_control_notation("1+0")
        else:
            return None


class ChessVariant(DisplayStringIntEnum):
    STANDARD = 0
    CHESS960 = 1
    SUICIDE = 2
    GIVEAWAY = 3
    ANTICHESS = 4
    ATOMIC = 5
    KINGOFTHEHILL = 6
    RACINGKINGS = 7
    HORDE = 8
    THREECHECK = 9
    CRAZYHOUSE = 10

    def get_board(self):
        if self is ChessVariant.CHESS960:
            return chess.Board
        return chess.variant.find_variant(self.name.lower())

    @property
    def is_drop_moves_supported(self):
        return self in {
            ChessVariant.CRAZYHOUSE,
        }

    @cached_property
    def _displayStringLabels(self):
        return {
            ChessVariant.STANDARD: _("Standard"),
            ChessVariant.CHESS960: _("Chess 960"),
            ChessVariant.SUICIDE: _("Suicide"),
            ChessVariant.GIVEAWAY: _("Give away"),
            ChessVariant.ANTICHESS: _("Anti chess"),
            ChessVariant.ATOMIC: _("Atomic"),
            ChessVariant.KINGOFTHEHILL: _("King of the hill"),
            ChessVariant.RACINGKINGS: _("Racing kings"),
            ChessVariant.HORDE: _("Horde"),
            ChessVariant.THREECHECK: _("Three check"),
            ChessVariant.CRAZYHOUSE: _("Crazy house"),
        }


class PlayerColor(DisplayStringIntEnum):
    RANDOM = 0
    WHITE = 1
    BLACK = 2

    @cached_property
    def _displayStringLabels(self):
        return {
            PlayerColor.RANDOM: _("Random"),
            PlayerColor.WHITE: _("White"),
            PlayerColor.BLACK: _("Black"),
        }

    def get_color(self):
        if self is PlayerColor.RANDOM:
            return random.choice(chess.COLORS)
        return chess.WHITE if self is PlayerColor.WHITE else chess.BLACK
