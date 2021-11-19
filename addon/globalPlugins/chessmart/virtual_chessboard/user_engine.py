# coding: utf-8

import os
import time
import threading
import subprocess
import functools
import dataclasses
import wx
import tones
import controlTypes
import queueHandler
import eventHandler
from logHandler import log
from ..helpers import import_bundled, GameSound, BIN_DIRECTORY
from ..signals import move_completed_signal, chessboard_opened_signal, game_started_signal, game_over_signal
from ..concurrency import call_threaded
from .user_driven import UserDrivenChessboard


STOCKFISH_EXECUTABLE_PATH = os.path.join(
    BIN_DIRECTORY, "stockfish_14", "stockfish_14_32bit.exe"
)
FAIRY_STOCKFISH_EXECUTABLE_PATH = os.path.join(
    BIN_DIRECTORY, "fairy_stockfish", "fairy-stockfish-largeboard_x86-64.exe"
)


with import_bundled():
    import chess
    import chess.engine


class UserEngineChessboard(UserDrivenChessboard):
    def __init__(self, *args, uci_options, uci_time_limit, **kwargs):
        super().__init__(*args, **kwargs)
        self.uci_options = uci_options or {}
        self.uci_time_limit = uci_time_limit or 2.0
        self.prospective = self.prospective if self.prospective is not None else True
        self.uci_engine = self.get_uci_engine(self._get_uci_engine_path())
        # Events
        move_completed_signal.connect(self.on_move_completed, sender=self)
        game_started_signal.connect(self.on_game_started, sender=self)
        game_over_signal.connect(self.on_game_over, sender=self)
        game_started_signal.send(self)

    def _get_uci_engine_path(self):
        if self.board.uci_variant == 'chess':
            return STOCKFISH_EXECUTABLE_PATH
        else:
            return  FAIRY_STOCKFISH_EXECUTABLE_PATH

    def get_uci_engine(self, executable):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        uci_engine = chess.engine.SimpleEngine.popen_uci(
            executable,
            creationflags=subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP,
            startupinfo=startupinfo,
            close_fds=True,
        )
        uci_engine.configure(self.uci_options)
        return uci_engine

    def on_game_over(self, sender, board_outcome):
        self.uci_engine.quit()

    def on_move_completed(self, sender, move, move_maker):
        if self.is_game_over:
            return
        if self.board.turn is not self.prospective:
            self.get_next_move_from_engine().add_done_callback(
                lambda future: wx.CallAfter(self.engine_play, future)
            )

    def engine_play(self, future):
        try:
            play_result = future.result()
        except chess.engine.EngineError:
            wx.CallAfter(self.game_error)
            return
        if play_result.resigned:
            wx.CallAfter(self.game_resigned)
        else:
            if play_result.draw_offered:
                self.draw_offered = True
            wx.CallAfter(self.move_piece_and_check_game_status, play_result.move)

    @call_threaded
    def get_next_move_from_engine(self):
        white_clock, black_clock = [
            self.time_control.chess_clocks[color] for color in chess.COLORS
        ]
        limit = chess.engine.Limit(
            time=self.uci_time_limit,
            white_clock=white_clock.remaining,
            black_clock=black_clock.remaining,
            white_inc=white_clock.increment,
            black_inc=black_clock.increment,
        )
        return self.uci_engine.play(
            self.board,
            limit,
        )

    def on_user_response_to_engine_draw_offer(self, engine_next_move, user_answer):
        if isinstance(self._current_focused_object, DrawChoiceMenu):
            self._current_focused_object = None
        if user_answer:
            self.game_drawn()
        else:
            self.move_piece_and_check_game_status(engine_next_move)

    def make_first_move(self):
        if self.prospective is not chess.BLACK:
            return

        def first_move_task():
            self.get_next_move_from_engine().add_done_callback(
                lambda future: wx.CallAfter(self.engine_play, future)
            )

        t = threading.Timer(interval=2, function=first_move_task)
        t.deamon = True
        t.start()

    def on_game_started(self, sender):
        queueHandler.queueFunction(queueHandler.eventQueue, self.make_first_move)
