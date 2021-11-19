# coding: utf-8

import typing as t
from ...algebraic_type import AlgebraicType, Variant
from ...time_control import ChessTimeControl
from ...helpers import import_bundled
from .client import InternetGameInfo


with import_bundled():
    import chess


class InternetChessAPIEvent(AlgebraicType):
    initialize_board = Variant(board_client="BoardClient")
    challenge_recieved = Variant(
        from_whom=str, playing_as_color=chess.Color, time_control=ChessTimeControl
    )
    challenge_cancelled = Variant(by_whom=str)
    challenge_accepted = Variant(by_whom=str)


class InternetChessBoardEvent(AlgebraicType):
    """Represents events related to a single game."""

    game_started = Variant(info=InternetGameInfo)
    game_drawn = Variant()
    game_time_forfeit = Variant(loser=chess.Color)
    game_resigned = Variant(loser=chess.Color)
    game_aborted = Variant(loser=chess.Color)
    move_made = Variant(move=chess.Move, player=chess.Color)
    clock_tick = Variant(time_control=ChessTimeControl)
    draw_offered = Variant(offered_by=chess.Color)
    draw_offer_rejected = Variant(rejected_by=chess.Color)
    chat_message_recieved = Variant(from_whom=str, message=str)
