# coding: utf-8

import os
import threading
import subprocess
import functools
import dataclasses
import wx
import tones
import controlTypes
import ui
import speech
import queueHandler
import eventHandler
from scriptHandler import script
from logHandler import log
from .ui_components import (
    MenuObject,
    MenuItemObject,
)
from ..helpers import import_bundled, GameSound, Color, speak_next
from .base import BaseChessboardCell, BaseVirtualChessboard
from .ui_components import SimpleList


with import_bundled():
    import chess



DROP_PIECE_TYPES =  (
    chess.PAWN,
    chess.KNIGHT,
    chess.BISHOP,
    chess.ROOK,
    chess.QUEEN,
)


class UserDrivenCell(BaseChessboardCell):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_dragging = False

    @property
    def states(self):
        states = {
            controlTypes.State.FOCUSABLE,
            controlTypes.State.FOCUSED,
        }
        if self.parent.is_game_over:
            return states.union(
                {
                    controlTypes.State.UNAVAILABLE,
                }
            )
        if self.parent.is_dragable(self.index):
            states.add(controlTypes.State.DRAGGABLE)
        if self.parent.is_drop_target(self.index):
            states.add(controlTypes.State.DROPTARGET)
        if self.is_dragging:
            states.add(controlTypes.State.DRAGGING)
        if self.parent.is_busy(self.index):
            states.add(controlTypes.State.BUSY)
        return states

    def event_gainFocus(self):
        super().event_gainFocus()
        if self.parent.is_drop_target(self.index):
            GameSound.drop_target.play()

    def get_highlight_color(self):
        is_drop_target = self.parent.is_drop_target(self.index)
        if is_drop_target:
            return Color.Green
        elif self is self.parent._dragged_cell:
            return Color.Purple
        elif self.parent._dragged_cell is None:
            return Color.Blue
        elif not is_drop_target:
            return Color.Red
        else:
            return super().get_highlight_color()

    def toggle_dragging(self, announce=True):
        self.is_dragging = not self.is_dragging
        if self.is_dragging:
            self.parent.set_dragged_cell(self)
            GameSound.pick_piece.play()
        else:
            self.parent.undrag_cell()
        if announce:
            eventHandler.executeEvent("stateChange", self)
        self.update_visuall_highlight()

    @script(gesture="kb:control+d")
    def script_make_draw_offer(self, gesture):
        if self.parent.is_game_over or not self.parent.can_draw:
            return
        if self.parent.draw_offered:
            self.parent.draw_offered = False
            ui.message("Draw offer withdrawn")
        else:
            ui.message("Draw offered.")
            self.parent.draw_offered = True

    @script(gesture="kb:f6")
    def script_my_pocket(self, gesture):
        self.parent.open_pocket(self.parent.prospective)

    @script(gesture="kb:shift+f6")
    def script_opponent_pocket(self, gesture):
        self.parent.open_pocket(not self.parent.prospective)

class UserDrivenChessboard(BaseVirtualChessboard):
    cell_class = UserDrivenCell

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dragged_cell = None
        self.draw_offered = False

    def get_highlighted_squares(self):
        yield from super().get_highlighted_squares()
        if self._dragged_cell is not None:
            yield self._dragged_cell.index

    def set_dragged_cell(self, cell):
        if self._dragged_cell:
            self._dragged_cell.toggle_dragging()
        self._dragged_cell = cell

    def undrag_cell(self):
        self._dragged_cell = None

    def activate_cell(self, cell):
        if self.is_game_over:
            GameSound.invalid.play()
            self.undrag_cell()
            return
        if self.is_busy(cell.index):
            GameSound.invalid.play()
            return
        piece = self.board.piece_at(cell.index)
        if piece is self._dragged_cell is None:
            if self.variant.is_drop_moves_supported:
                self.try_make_drop_move(cell.index)
                return
            GameSound.invalid.play()
            return
        elif self.is_dragable(cell.index):
            cell.toggle_dragging()
        elif self.is_drop_target(cell.index):
            self.user_play(self._dragged_cell.index, cell.index)
            self._dragged_cell.toggle_dragging()
            eventHandler.queueEvent("stateChange", cell)
        else:
            GameSound.invalid.play()

    def is_dragable(self, index):
        piece = self.board.piece_at(index)
        return (
            (piece is not None)
            and (piece.color is self.prospective)
            and (not self.is_busy(index))
        )

    def is_drop_target(self, index):
        if self._dragged_cell is None:
            if self.variant.is_drop_moves_supported:
                return self._is_drop_move_drop_target(index)
            return False
        move = chess.Move(self._dragged_cell.index, index)
        if move in self.board.legal_moves:
            return True
        elif self.is_promotion_move(move):
            return True
        else:
            return False

    def is_busy(self, index):
        return self.board.turn != self.prospective

    def is_promotion_move(self, move):
        return (move.promotion is not None) or (
            dataclasses.replace(move, promotion=chess.QUEEN) in self.board.legal_moves
        )

    def _is_drop_move_drop_target(self, index):
        if index in self.board.legal_drop_squares():
            return any(self.get_available_droppable_pieces(self.prospective))
        return False

    def user_play(self, from_index, to_index):
        move = chess.Move(from_index, to_index)
        if move not in self.board.legal_moves and self.is_promotion_move(move):
            p_menu = PromotionMenu(
                user_choice_callback=functools.partial(self.make_promotion_move, move),
                name="Promote Pawn. Select promotion piece type:",
                parent=self,
            )
            eventHandler.queueEvent("gainFocus", p_menu)
        else:
            self.move_piece_and_check_game_status(move)

    def try_make_drop_move(self, index):
        if not self._is_drop_move_drop_target(index):
            GameSound.invalid.play()
            return
        available_piece_types = self.get_available_droppable_pieces(self.prospective)
        drop_menu = DropPieceMenu(
            available_piece_types=available_piece_types,
            user_choice_callback=functools.partial(self.make_drop_move, index),
            name="Drop Piece. Select piece type:",
            parent=self,
        )
        eventHandler.queueEvent("gainFocus", drop_menu)

    def make_drop_move(self, index, piece_type):
        move = chess.Move(
            from_square=index,
            to_square=index,
            drop=piece_type
        )
        self.move_piece_and_check_game_status(move)

    def make_promotion_move(self, move, promotion_piece_type):
        promotion_move = dataclasses.replace(move, promotion=promotion_piece_type)
        queueHandler.queueFunction(
            queueHandler.eventQueue,
            self.move_piece_and_check_game_status,
            promotion_move,
        )

    def make_opponent_draw_offer(self):
        color_name = self.game_announcer.color_name(not self.prospective)
        self._current_focused_object = DrawChoiceMenu(
            choice_callback=self.draw_offer_callback,
            name=f"{color_name} is offering to draw. Do you want to accept the draw offer?",
            parent=self,
        )
        GameSound.request_promotion.play()
        eventHandler.queueEvent("gainFocus", self._current_focused_object)

    def draw_offer_callback(self, accepted: bool):
        if isinstance(self._current_focused_object, DrawChoiceMenu):
            self._current_focused_object = None
        if accepted:
            self.game_drawn()

    def open_pocket(self, color: chess.Color):
        if not self.variant.is_drop_moves_supported:
            return
        color_name = self.game_announcer.color_name(color)
        pieces = self.get_available_droppable_pieces(color)
        if not pieces:
            speak_next([
                speech.commands.WaveFileCommand(GameSound.invalid.filename),
                _("{color}'s pocket is empty").format(color=color_name)
            ])
            return
        pocket_list_name = _("{color}'s pocket").format(color=color_name)
        pocket_list = SimpleList(parent=self, name=pocket_list_name, close_gesture="kb:f6")
        pocket = self.board.pockets[color].pieces
        for (ptype, pcount) in zip(pieces, (pocket[p] for p in pieces)):
            if pcount == 1:
                pocket_list.add_item(_("{count} {piece}").format(count=pcount, piece=self.game_announcer.piece_name(ptype)))
            else:
                pocket_list.add_item(_("{count} {piece}s").format(count=pcount, piece=self.game_announcer.piece_name(ptype)))
        eventHandler.queueEvent("gainFocus", pocket_list)

    def get_available_droppable_pieces(self, color):
        return tuple(
            piece_type
            for (piece_type, piece_count) in self.board.pockets[color].pieces.items()
            if piece_count
        )

class PieceSelectionMenu(MenuObject):
    available_piece_types  = []

    def __init__(self, user_choice_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_choice_callback = user_choice_callback
        self.init_container_state(
            [
                PieceSelectionMenuItem(
                    piece_type=piece_type,
                    name=chess.piece_name(piece_type),
                    parent=self,
                )
                for piece_type in self.available_piece_types
            ]
        )

    def on_item_activated(self, item):
        self.user_choice_callback(item.piece_type)
        self.close_menu()

    def event_gainFocus(self):
        super().event_gainFocus()
        queueHandler.queueFunction(
            queueHandler.eventQueue, GameSound.request_promotion.play
        )


class PieceSelectionMenuItem(MenuItemObject):
    def __init__(self, piece_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.piece_type = piece_type


class PromotionMenu(PieceSelectionMenu):
    available_piece_types  = [
        chess.QUEEN,
        chess.KNIGHT,
        chess.BISHOP,
        chess.ROOK,
    ]


class DrawChoiceMenu(MenuObject):
    def __init__(self, choice_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choice_callback = choice_callback
        self.init_container_state(
            [
                MenuItemObject(name="No, decline offer and continue game", parent=self),
                MenuItemObject(name="Yes, accept offer and end game", parent=self),
            ]
        )

    def on_item_activated(self, item):
        self.choice_callback(bool(self.index_of(item)))
        eventHandler.queueEvent("gainFocus", self.parent)

    def close_menu(self):
        return


class DropPieceMenu(PieceSelectionMenu):

    def __init__(self, *args, available_piece_types, **kwargs):
        self.available_piece_types = available_piece_types
        super().__init__(*args, **kwargs)
