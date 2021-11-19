# coding: utf-8

from .helpers import import_bundled


with import_bundled():
    import blinker


Chessboard_signals = blinker.Namespace()
chessboard_opened_signal = Chessboard_signals.signal("chessboard-opened")
chessboard_closed_signal = Chessboard_signals.signal("chessboard-closed")
game_started_signal = Chessboard_signals.signal("game-started")
game_over_signal = Chessboard_signals.signal("game_over", "args: outcome")
move_completed_signal = Chessboard_signals.signal(
    "move-completed", doc="args: move_maker"
)
