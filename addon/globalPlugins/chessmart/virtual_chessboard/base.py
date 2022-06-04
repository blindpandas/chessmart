# coding: utf-8

import sys
import os
import math
import functools
import itertools
import bisect
import dataclasses
import wx
import tones
import inputCore
import globalVars
import ui
import api
import controlTypes
import queueHandler
import eventHandler
import speech
import speech.commands
from NVDAObjects import NVDAObject
from scriptHandler import script
from logHandler import log
from .ui_components import (
    KeyboardNavigableNVDAObjectMixin,
    MenuObject,
    MenuItemObject,
    SimpleList,
)
from ..time_control import ChessTimeControl, NULL_TIME_CONTROL
from ..spoken_messages import standard_game_announcer, ibca_game_announcer
from ..helpers import import_bundled, intersperse, GameSound, speak_next, Color
from ..concurrency import call_threaded
from ..signals import (
    move_completed_signal,
    game_started_signal,
    game_over_signal,
    chessboard_opened_signal,
    chessboard_closed_signal,
)


with import_bundled():
    import chess
    import chess.pgn
    import chess.svg


class BaseChessboardCell(KeyboardNavigableNVDAObjectMixin, NVDAObject):
    role = controlTypes.Role.TABLECELL
    PIECE_LETTERS = {
        "r": chess.ROOK,
        "n": chess.KNIGHT,
        "b": chess.BISHOP,
        "q": chess.QUEEN,
        "k": chess.KING,
        "p": chess.PAWN,
    }

    def __init__(self, parent, index, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.game_announcer = self.parent.game_announcer
        self.index = index
        self.processID = self.parent.processID
        self._add_multiple_scripts()

    def _add_multiple_scripts(self):
        gestures = {}
        jump_script_func = getattr(self.__class__, "script_jump_to_piece_handler")
        for letter, piece_type in self.PIECE_LETTERS.items():
            gestures[f"kb:{letter}"] = functools.partialmethod(
                jump_script_func, piece_type, False
            )
            gestures[f"kb:shift+{letter}"] = functools.partialmethod(
                jump_script_func, piece_type, True
            )
        self._gestureMap.update(
            {inputCore.normalizeGestureIdentifier(k): v for (k, v) in gestures.items()}
        )

    @property
    def roleText(self):
        if self.parent.board.piece_at(self.index) is None:
            return "Square"

    @property
    def states(self):
        return {
            controlTypes.State.FOCUSABLE,
            controlTypes.State.FOCUSED,
        }

    @property
    def description(self):
        return self.game_announcer.square_name(self.index)

    @property
    def name(self):
        return self.parent.get_piece_name_at_square(self.index)

    def on_activate(self):
        self.parent.activate_cell(self)

    @property
    def square_color(self):
        square_number = self.index
        file_index, rank_index = (
            chess.square_file(square_number) + 1,
            chess.square_rank(square_number) + 1,
        )
        is_row_even = (file_index % 2) == 0
        is_cell_even = (rank_index % 2) == 0
        return chess.WHITE if (is_row_even != is_cell_even) else chess.BLACK

    def get_remaining_time(self, color: chess.Color):
        color_name = chess.COLOR_NAMES[color]
        total_seconds = self.parent.time_control.get_remaining_time()[color]
        minutes = math.floor(total_seconds / 60)
        seconds = math.floor(total_seconds % 60)
        if not minutes:
            return f"{seconds} seconds remaining for {color_name}"
        elif not seconds:
            return f"{minutes} minutes remaining for {color_name}"
        return f"{minutes} minutes and {seconds} seconds remaining for {color_name}"

    def get_highlight_color(self):
        return Color.Blue

    def update_visuall_highlight(self):
        if not self.parent.use_visuals:
            return
        arrows = [
            chess.svg.Arrow(
                self.index, self.index, color=self.get_highlight_color().value
            )
        ]
        last_move = None
        if self.parent.board.move_stack:
            last_move = self.parent.board.move_stack[-1]
            if self.parent.visual_arrows:
                arrows.append(
                    chess.svg.Arrow(
                        last_move.from_square,
                        last_move.to_square,
                        color=Color.DarkGray.value,
                    )
                )
        self.parent.dialog.set_board_image(arrows=arrows, lastmove=last_move)

    def event_gainFocus(self):
        super().event_gainFocus()
        self.parent._focused_cell = self.index
        if self.square_color is chess.BLACK:
            GameSound.black_square.play()
        self.update_visuall_highlight()

    def script_activate_cell(self, gesture):
        self.on_activate()

    def script_jump_to_piece_handler(self, piece_type, to_opponent_piece, gesture):
        if self.parent.prospective is not None:
            piece_color = self.parent.prospective
        else:
            piece_color = chess.WHITE
        piece_color = piece_color if not to_opponent_piece else not piece_color
        self.parent.jump_to_piece(piece_type, piece_color)

    @script(gesture="kb:f1")
    def script_player_overview(self, gesture):
        self.parent.announce_player_overview(self.parent.prospective)

    @script(gesture="kb:shift+f1")
    def script_opponent_overview(self, gesture):
        self.parent.announce_player_overview(not self.parent.prospective)

    @script(gesture="kb:f3")
    def script_cell_info(self, gesture):
        color = chess.COLOR_NAMES[self.square_color]
        spoken_commands = [
            ibca_game_announcer.square_file(self.index),
            speech.commands.BreakCommand(100),
            ibca_game_announcer.square_rank(self.index),
            speech.commands.BreakCommand(250),
            f"square color: {color},",
        ]
        piece_type = self.parent.board.piece_type_at(self.index)
        if piece_type is not None:
            spoken_commands.insert(0, ibca_game_announcer.piece_name(piece_type))
            spoken_commands.insert(1, speech.commands.BreakCommand(100))
        speak_next(spoken_commands)

    @script(gesture="kb:f2")
    def script_announce_time_for_current_turn(self, gesture):
        if self.parent.time_control is NULL_TIME_CONTROL:
            GameSound.invalid.play()
            return ui.message("No Time Control")
        color = self.parent.board.turn
        remaining = self.get_remaining_time(color)
        ui.message(remaining)

    @script(gesture="kb:shift+f2")
    def script_announce_time_for_other_turn(self, gesture):
        if self.parent.time_control is NULL_TIME_CONTROL:
            GameSound.invalid.play()
            return ui.message("No Time Control")
        color = not self.parent.board.turn
        remaining = self.get_remaining_time(color)
        ui.message(remaining)

    @script(gesture="kb:a")
    def script_announce_attackers(self, gesture):
        self.parent.announce_attackers(self.index)

    @script(gesture="kb:f4")
    def script_score_sheet(self, gesture):
        if self.parent.score_sheet_menu:
            eventHandler.queueEvent("gainFocus", self.parent.score_sheet_menu)
        else:
            ui.message("Score sheet is empty")

    @script(gesture="kb:control+s")
    def script_save_board_pgn(self, gesture):
        if globalVars.appArgs.secure:
            return ui.message("Could not save game. NVDA running in secure mode.")
        self.parent.save_game()

    @script(gesture="kb:control+shift+s")
    def script_save_board_image(self, gesture):
        if globalVars.appArgs.secure:
            return ui.message("Could not save game. NVDA running in secure mode.")
        self.parent.save_board_image()

    @script(gesture="kb:escape")
    def script_escape(self, gesture):
        self.parent.hide_board_gui()

    @script(gesture="kb:rightarrow")
    def script_rightarrow(self, gesture):
        if not self.parent.is_board_flipped:
            self.parent.navigate_right(self)
        else:
            self.parent.navigate_left(self)

    @script(gesture="kb:leftarrow")
    def script_leftarrow(self, gesture):
        if not self.parent.is_board_flipped:
            self.parent.navigate_left(self)
        else:
            self.parent.navigate_right(self)

    @script(gesture="kb:downarrow")
    def script_downarrow(self, gesture):
        if not self.parent.is_board_flipped:
            self.parent.navigate_down(self)
        else:
            self.parent.navigate_up(self)

    @script(gesture="kb:uparrow")
    def script_uparrow(self, gesture):
        if not self.parent.is_board_flipped:
            self.parent.navigate_up(self)
        else:
            self.parent.navigate_down(self)

    __gestures = {
        "kb:enter": "activate_cell",
        "kb:numpadenter": "activate_cell",
        "kb:space": "activate_cell",
    }


class BaseVirtualChessboard(KeyboardNavigableNVDAObjectMixin, NVDAObject):
    role = controlTypes.Role.TABLE
    roleText = "Board"
    name = "Chess"
    row_ranges = tuple(
        range(i, j)
        for (i, j) in zip([i * 8 for i in range(0, 8)], [j * 8 for j in range(1, 9)])
    )
    cell_class = BaseChessboardCell
    can_draw = True
    can_resign = True

    def __init__(
        self,
        dialog,
        *,
        variant,
        prospective=None,
        time_control=NULL_TIME_CONTROL,
        game_announcer=standard_game_announcer,
        use_visuals=True,
        visual_arrows=False,
        pychess_board=None,
    ):
        super().__init__()
        self.parent = api.getFocusObject()
        self.processID = self.parent.processID
        self.dialog = dialog
        self.variant = variant
        self.game_announcer = game_announcer
        self.prospective = prospective
        self.time_control = time_control
        self.use_visuals = use_visuals
        self.visual_arrows = visual_arrows
        self.board = pychess_board or chess.Board()
        self._chess_cells = [
            self.cell_class(parent=self, index=i) for i in range(0, 64)
        ]
        self._focused_cell = self.get_initial_focus_cell()
        self.is_game_over = False
        self._current_focused_object = None
        self.score_sheet_menu = SimpleList(
            parent=self, name="Score sheet", close_gesture="kb:f4"
        )
        # Connect to events
        game_started_signal.connect(
            lambda s: self.time_control.start_game(), sender=self, weak=False
        )
        chessboard_closed_signal.connect(
            lambda s: self.game_over(), sender=self, weak=False
        )

    def get_initial_focus_cell(self):
        return 4 if not self.is_board_flipped else 60

    @property
    def is_board_flipped(self):
        return self.prospective == False

    @property
    def is_board_visually_flipped(self):
        return self.is_board_flipped

    def get_highlighted_squares(self):
        if self._focused_square is not None:
            yield self._focused_square.index

    def get_containing_row(self, index):
        for rng in self.row_ranges:
            if index in rng:
                return rng

    def game_over(self, dialog_title="Game Over"):
        self.is_game_over = True
        self.dialog.SetTitle(dialog_title)
        eventHandler.queueEvent("stateChange", api.getFocusObject())
        game_over_signal.send(self, board_outcome=self.board.outcome())

    def game_resigned(self, resigning_color):
        self.game_over()
        color_name = chess.COLOR_NAMES[resigning_color]
        self.dialog.SetTitle(f"{color_name} resigned")
        speak_next(
            [
                speech.commands.WaveFileCommand(GameSound.resigned.filename),
                speech.commands.BreakCommand(200),
                f"{color_name} resigned the game",
            ]
        )

    def game_drawn(self):
        self.game_over()
        self.dialog.SetTitle("Game Drawn")
        speak_next(
            [
                speech.commands.WaveFileCommand(GameSound.drawn.filename),
                speech.commands.BreakCommand(200),
                "Game is drawn",
            ]
        )

    def game_time_forfeit(self, losing_color: chess.Color):
        self.game_over(
            f"Game Over: Time Forfeit - {self.game_announcer.color_name(not losing_color)} is the winner"
        )
        speak_next(
            [
                speech.commands.WaveFileCommand(GameSound.time_forfeit.filename),
                speech.commands.BreakCommand(300),
                self.game_announcer.color_name(losing_color),
                speech.commands.BreakCommand(100),
                "time over",
                speech.commands.BreakCommand(150),
                self.game_announcer.color_name(not losing_color),
                speech.commands.BreakCommand(100),
                "is the winner",
            ]
        )

    def game_error(self, error_message="Game terminated due to an error"):
        self.game_over()
        self.dialog.SetTitle(error_message)
        speak_next(
            [
                speech.commands.WaveFileCommand(GameSound.error.filename),
                speech.commands.BreakCommand(200),
                error_message,
            ]
        )

    def set_focus_to_cell(self, index):
        eventHandler.executeEvent("gainFocus", self._chess_cells[index])

    def activate_cell(self, cell):
        GameSound.invalid.play()

    def move_piece_and_check_game_status(self, move, pre_speech=(), post_speech=()):
        if move not in self.board.legal_moves:
            speak_next(
                [
                    speech.commands.WaveFileCommand(GameSound.invalid.filename),
                    speech.commands.BreakCommand(100),
                    "Illegal move",
                ]
            )
            return
        move_maker = self.board.turn
        old_piece_at_from_square = self.board.piece_at(move.from_square)
        old_piece_at_target_square = self.board.piece_at(move.to_square)
        is_castling = self.board.is_castling(move)
        is_king_side_castling = (
            False if not is_castling else self.board.is_kingside_castling(move)
        )
        is_en_passant = self.board.is_en_passant(move)
        if is_en_passant:
            old_piece_at_target_square = self.board.piece_at(move.to_square - 8)
        self.board.push(move)
        self.time_control.time_move(
            not self.board.turn, total_moves=len(self.board.move_stack)
        )
        desc_generator = tuple(
            self._get_move_description(
                move,
                move_maker,
                old_piece_at_target_square,
                old_piece_at_from_square,
                is_castling,
                is_king_side_castling,
                is_en_passant,
            )
        )
        self.score_sheet_menu.add_item(
            " ".join(i for i in desc_generator if type(i) is str)
        )
        spoken_commands = [desc_generator]
        spoken_commands.append(pre_speech)
        if self.board.is_game_over():
            spoken_commands.append(self._get_game_over_messages())
            spoken_commands.append([speech.commands.CallbackCommand(self.game_over)])
        elif self.board.is_check():
            color_in_check = chess.COLOR_NAMES[self.board.turn]
            spoken_commands.append(
                [
                    speech.commands.WaveFileCommand(GameSound.check.filename),
                    speech.commands.BreakCommand(250),
                    color_in_check,
                    speech.commands.BreakCommand(200),
                    f"is in Check",
                ]
            )
            if (move_maker != self.prospective) or (self.prospective is None):
                spoken_commands.append(
                    [
                        speech.commands.BreakCommand(250),
                        speech.commands.CallbackCommand(
                            functools.partial(
                                self.jump_to_piece, chess.KING, self.board.turn
                            )
                        ),
                        speech.commands.BreakCommand(250),
                        speech.commands.CallbackCommand(
                            functools.partial(
                                self.announce_attackers,
                                self.board.king(self.board.turn),
                                True,
                            )
                        ),
                    ]
                )
        spoken_commands.append(post_speech)
        speak_next(itertools.chain(*spoken_commands))
        self.dialog.set_board_image(lastmove=move)
        move_completed_signal.send(self, move=move, move_maker=move_maker)

    def _get_move_description(
        self,
        move,
        move_maker,
        old_piece_at_target_square,
        old_piece_at_from_square,
        is_castling,
        is_king_side_castling,
        is_en_passant,
    ):
        if move.promotion is not None:
            yield from [
                speech.commands.WaveFileCommand(GameSound.promotion.filename),
                speech.commands.BreakCommand(300),
            ]
            yield from intersperse(
                self.game_announcer.promotion_move(move, move_maker=move_maker),
                speech.commands.BreakCommand(200),
            )
            return
        if not is_castling:
            yield from self._get_move_message(
                move, move_maker, old_piece_at_target_square, is_en_passant
            )
        else:
            yield from (
                speech.commands.WaveFileCommand(GameSound.castling.filename),
                speech.commands.BreakCommand(250),
            )
            yield from intersperse(
                self.game_announcer.castling_move(move_maker, is_king_side_castling),
                speech.commands.BreakCommand(200),
            )

    def _get_move_message(
        self, move, move_maker, old_piece_at_target_square, is_en_passant
    ):
        moved_piece = self.board.piece_at(move.to_square)
        if move.drop:
            yield speech.commands.WaveFileCommand(GameSound.drop_move.filename)
            yield from intersperse(
                self.game_announcer.drop_move(move_maker, move=move),
                speech.commands.BreakCommand(200),
            )
            yield speech.commands.BreakCommand(300)
        if old_piece_at_target_square is not None:
            capture_sound = (
                GameSound.capture if not is_en_passant else GameSound.en_passant
            )
            spoken_commands = [
                speech.commands.WaveFileCommand(capture_sound.filename),
            ]
            spoken_commands += intersperse(
                self.game_announcer.capture_move(
                    move,
                    moved_piece,
                    old_piece_at_target_square,
                ),
                speech.commands.BreakCommand(200),
            )
            if is_en_passant:
                spoken_commands.append("en passant")
            yield from spoken_commands
        else:
            yield speech.commands.WaveFileCommand(GameSound.drop_piece.filename)
            yield from intersperse(
                self.game_announcer.normal_move(
                    move,
                    moved_piece,
                    move_maker=move_maker,
                ),
                speech.commands.BreakCommand(50),
            )

    def jump_to_piece(self, piece_type, piece_color):
        target_squares = tuple(self.board.pieces(piece_type, piece_color))
        if not target_squares:
            piece = chess.Piece(piece_type, piece_color)
            piece_name = self.game_announcer.describe_piece(piece)
            ui.message(f"No {piece_name}")
            return
        target_pos = bisect.bisect_right(target_squares, self._focused_cell)
        if target_pos == len(target_squares):
            target_pos = 0
        target_cell = target_squares[target_pos]
        self.set_focus_to_cell(target_cell)

    def notify_invalid_navigation(self):
        GameSound.invalid.play()
        speech.speakObject(api.getFocusObject(), controlTypes.OutputReason.FOCUS)

    def get_piece_name_at_square(self, index):
        piece = self.board.piece_at(index)
        if piece is None:
            return ""
        return self.game_announcer.describe_piece(piece)

    def _get_game_over_messages(self):
        outcome = self.board.outcome()
        termination_reason = outcome.termination.name.replace("_", " ")
        yield from [
            speech.commands.WaveFileCommand(GameSound.game_over.filename),
            speech.commands.BreakCommand(250),
            termination_reason,
        ]
        game_winner = (
            ""
            if outcome.winner is None
            else self.game_announcer.color_name(outcome.winner)
        )
        if game_winner:
            yield from [
                speech.commands.BreakCommand(250),
                f"{game_winner}",
                speech.commands.BreakCommand(200),
                "is the winner",
            ]

    def announce_attackers(self, cell_index, announce_piece_name=False):
        piece = self.board.piece_at(cell_index)
        if piece is not None:
            attacking_color = not piece.color
            attackers = list(self.board.attackers(attacking_color, cell_index))
        else:
            attackers = list(self.board.attackers(not self.board.turn, cell_index))
        attackers.sort()
        if not attackers:
            ui.message("This square is not under attack")
            return
        spoken_commands = []
        if announce_piece_name:
            piece_name = self.get_piece_name_at_square(cell_index)
            spoken_commands.append(f"{piece_name}")
            spoken_commands.append(speech.commands.BreakCommand(250))
        spoken_commands += [
            "Attacked by",
            speech.commands.BreakCommand(250),
        ]
        for attacking_square in attackers:
            square_name = chess.square_name(attacking_square)
            piece_name = self.get_piece_name_at_square(attacking_square)
            spoken_commands += [
                piece_name,
                speech.commands.BreakCommand(250),
                "at",
                speech.commands.BreakCommand(250),
                square_name,
            ]
            spoken_commands.append(speech.commands.BreakCommand(350))
        speak_next(spoken_commands)

    def announce_player_overview(self, color):
        square_set = itertools.chain(
            *[self.board.pieces(piece_type, color) for piece_type in sorted(chess.PIECE_TYPES, reverse=True)]
        )
        spoken_commands = [
            f"{self.get_piece_name_at_square(square)}, {self.game_announcer.square_name(square)}"
            for square in square_set
        ]
        speak_next(intersperse(spoken_commands, speech.commands.BreakCommand(250)))

    def event_gainFocus(self):
        if self._current_focused_object is not None:
            eventHandler.queueEvent("gainFocus", self._current_focused_object)
        else:
            self.set_focus_to_cell(self._focused_cell)

    def navigate_left(self, anchor):
        row_range = self.get_containing_row(anchor.index) or range(0, 63)
        prev_index = anchor.index - 1
        if prev_index not in row_range:
            return self.notify_invalid_navigation()
        self.set_focus_to_cell(prev_index)

    def navigate_right(self, anchor):
        row_range = self.get_containing_row(anchor.index) or range(0, 63)
        next_index = anchor.index + 1
        if next_index not in row_range:
            return self.notify_invalid_navigation()
        self.set_focus_to_cell(next_index)

    def navigate_up(self, anchor):
        next_index = anchor.index + 8
        if next_index > 63:
            return self.notify_invalid_navigation()
        self.set_focus_to_cell(next_index)

    def navigate_down(self, anchor):
        prev_index = anchor.index - 8
        if prev_index < 0:
            return self.notify_invalid_navigation()
        self.set_focus_to_cell(prev_index)

    def hide_board_gui(self):
        eventHandler.queueEvent("gainFocus", self.parent)
        self.dialog.Hide()

    @call_threaded
    def save_game(self):
        saveFileDialog = wx.FileDialog(
            parent=None,
            message="Save Game As",
            defaultDir=wx.GetUserHome(),
            wildcard="Chess Game *.pgn | *.pgn",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        with saveFileDialog as save_dialog:
            if save_dialog.ShowModal() != wx.ID_OK:
                return
            save_as_filename = save_dialog.GetPath().strip()
        if not save_as_filename:
            return
        game = chess.pgn.Game.from_board(self.board)
        with open(save_as_filename, "w", encoding="utf-8") as file:
            exporter = chess.pgn.FileExporter(file)
            game.accept(exporter)

    @call_threaded
    def save_board_image(self):
        saveFileDialog = wx.FileDialog(
            parent=None,
            message="Save Board To Image",
            defaultDir=wx.GetUserHome(),
            wildcard="Portable Network Graphics *.png | *.png",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        with saveFileDialog as save_dialog:
            if save_dialog.ShowModal() != wx.ID_OK:
                return
            save_as_filename = save_dialog.GetPath().strip()
        if not save_as_filename:
            return
        self.dialog.bitmap_buffer.SaveFile(save_as_filename, wx.BITMAP_TYPE_PNG)
