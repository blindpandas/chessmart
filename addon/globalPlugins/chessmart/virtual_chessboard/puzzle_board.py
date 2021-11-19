# coding: utf-8

import tones
import wx
import dataclasses
import typing as t
import functools
import queueHandler
import ui
import speech
from scriptHandler import script
from ..signals import game_started_signal
from ..helpers import import_bundled, GameSound, speak_next
from ..puzzle import Puzzle
from .user_driven import UserDrivenChessboard


with import_bundled():
    import chess


class PuzzleChessboard(UserDrivenChessboard):

    def __init__(self, *args, puzzle: Puzzle, **kwargs):
        super().__init__(*args, **kwargs)
        self.prospective = not self.board.turn
        self.puzzle = puzzle
        wx.CallLater(2000, self._perform_first_move)

    def _perform_first_move(self):
        king_square = self.board.king(self.prospective)
        king_square_focus_callback = functools.partial(self.set_focus_to_cell, king_square)
        color_name = self.game_announcer.color_name(self.prospective)
        post_speech = [
            "",
            speech.commands.BreakCommand(500),
            _("{color} to move").format(color=color_name),
            speech.commands.BreakCommand(300),
            speech.commands.CallbackCommand(king_square_focus_callback),
        ]
        self.move_piece_and_check_game_status(
            self.puzzle.auto_performed_move,
            pre_speech=(),
            post_speech=post_speech
        )

    def move_piece_and_check_game_status(self, move, pre_speech=(), post_speech=()):
        if self.board.turn == self.prospective:
            if move in self.puzzle.solution_moves:
                post_speech = list(post_speech) + [
                    speech.commands.BreakCommand(500),
                    "Well done!",
                    speech.commands.BreakCommand(250),
                    "Puzzle Solved",
                    speech.commands.BreakCommand(100),
                    speech.commands.WaveFileCommand(GameSound.puzzle_solved.filename),
                    speech.commands.CallbackCommand(lambda: self.game_over("Puzzle Solved"))
                ]
            else:
                speak_next([
                    speech.commands.WaveFileCommand(GameSound.invalid.filename),
                    f"{move} is not the expected move"
                ])
                return
        super().move_piece_and_check_game_status(move, pre_speech, post_speech)
