# coding: utf-8

import tones
import wx
import dataclasses
import typing as t
import functools
import queueHandler
import ui
import speech
from scriptHandler import script, getLastScriptRepeatCount
from ..signals import game_started_signal
from ..helpers import import_bundled, GameSound, speak_next, intersperse
from ..puzzle_database import PuzzleSet
from .user_driven import UserDrivenChessboard, UserDrivenCell

with import_bundled():
    import chess



class PuzzleCell(UserDrivenCell):
    @script(gesture="kb:control+f1")
    def script_puzzle_info(self, gesture):
        puzzle = self.parent.puzzle
        spoken_msgs = [
            _("{category}: {description}").format(category=label, description=description)
            for (label, description) in puzzle.get_theme_info()
        ] + [
            _("Rating: {rating}").format(rating=puzzle.rating),
            speech.commands.BreakCommand(100),
            _("Puzzle ID: {puzzle_id}").format(puzzle_id=puzzle.puzzle_id),
        ]
        speak_next(intersperse(spoken_msgs, speech.commands.BreakCommand(100)))

    @script(gesture="kb:control+enter")
    def script_solve_puzzle(self, gesture):
        solution_move = self.parent.puzzle.solution_moves[0]
        if self.parent.board.move_stack[-1] == solution_move:
            speak_next([
                speech.commands.WaveFileCommand(GameSound.invalid.filename),
                "Puzzle is already solved",
            ])
            return
        if getLastScriptRepeatCount() > 0:
            self.parent.move_piece_and_check_game_status(solution_move, auto_solved=True)
        else:
            speak_next(["Press twice to execute the solution move"])


class PuzzleChessboard(UserDrivenChessboard):
    cell_class = PuzzleCell
    can_draw = False
    can_resign = False

    def __init__(self, *args, puzzles: PuzzleSet, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.puzzles = puzzles.load_history()
        except FileNotFoundError:
            self.puzzles = puzzles
        self.puzzle = None
        self.next_puzzle()

    def hide_board_gui(self):
        self.puzzles.save_history()
        super().hide_board_gui()

    def next_puzzle(self):
        if self.puzzle is None:
            pre_speech = [
                "Loading puzzle",
            ]
        else:
            pre_speech = [
                "Loading next puzzle",
            ]
        try:
            self.puzzle = next(self.puzzles)
        except StopIteration:
            speak_next([
                "All Done",
                speech.commands.WaveFileCommand(GameSound.drawn.filename),
            ])
            self.game_over("Puzzle Completed")
        else:
            if self.is_game_over:
                self.is_game_over = False
            self.board.reset()
            self.board.set_fen(self.puzzle.fen)
            self.prospective = not self.board.turn
            self.score_sheet_menu.clear()
            queueHandler.queueFunction(queueHandler.eventQueue, speak_next, pre_speech)
            wx.CallLater(2000, self._perform_puzzle_first_move)

    def _perform_puzzle_first_move(self):
        king_square = self.board.king(self.prospective)
        king_square_focus_callback = functools.partial(self.set_focus_to_cell, king_square)
        color_name = self.game_announcer.color_name(self.prospective)
        post_speech = [
            "",
            speech.commands.BreakCommand(500),
            _("{color} to move").format(color=color_name),
            speech.commands.BreakCommand(100),
            speech.commands.CallbackCommand(king_square_focus_callback),
        ]
        self.move_piece_and_check_game_status(
            self.puzzle.auto_performed_move,
            pre_speech=(),
            post_speech=post_speech
        )

    def move_piece_and_check_game_status(self, move, pre_speech=(), post_speech=(), auto_solved=False):
        if self.board.turn == self.prospective:
            if move in self.puzzle.solution_moves:
                puzzle_messages = [
                    speech.commands.BreakCommand(500),
                    speech.commands.WaveFileCommand(GameSound.puzzle_solved.filename),
                    speech.commands.BreakCommand(200),
                    "Puzzle Solved",
                    speech.commands.BreakCommand(300),
                    speech.commands.CallbackCommand(self.next_puzzle)
                ]
                if not auto_solved:
                    puzzle_messages.insert(1,  "Well done!")
                    puzzle_messages.insert(1,  speech.commands.BreakCommand(250))
                post_speech = list(post_speech) + puzzle_messages
            else:
                speak_next([
                    speech.commands.WaveFileCommand(GameSound.invalid.filename),
                    f"{move} is not the expected move"
                ])
                return
        super().move_piece_and_check_game_status(move, pre_speech, post_speech)
