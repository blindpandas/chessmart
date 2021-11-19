# coding: utf-8

import functools
import wx
import tones
import gui
import ui
import controlTypes
import queueHandler
import eventHandler
import speech.commands
from scriptHandler import script
from logHandler import log
from ..helpers import import_bundled, speak_next, GameSound
from ..signals import move_completed_signal, chessboard_opened_signal
from .ui_components import SimpleList
from .user_driven import UserDrivenChessboard, UserDrivenCell


with import_bundled():
    import chess


class InternetChessboardCell(UserDrivenCell):
    @script(gesture="kb:control+shift+r")
    def script_resign_game(self, gesture):
        """Resigns the game."""
        ui.message("Resigning...")
        self.parent.client.resign_game().add_done_callback(
            lambda f: GameSound.resigned.play()
        )

    @script(gesture="kb:control+shift+d")
    def script_offer_draw(self, gesture):
        self.parent.client.offer_draw().add_done_callback(self._on_draw_callback)

    @script(gesture="kb:c")
    def script_send_chat_message(self, gesture):
        dialog = wx.TextEntryDialog(
            gui.mainFrame,
            _("Enter chat message"),
            _("Chat"),
        )
        gui.runScriptModalDialog(
            dialog, callback=functools.partial(self._on_chat_before_send, dialog)
        )

    @script(gesture="kb:f5")
    def script_show_chat_list(self, gesture):
        if self.parent.chat_list:
            eventHandler.queueEvent("gainFocus", self.parent.chat_list)
        else:
            ui.message(_("No chat messages"))

    def _on_chat_before_send(self, dialog, retval):
        if retval == wx.ID_OK:
            tones.beep(400, 400)
        message = dialog.GetValue().strip()
        if message:
            self.parent.client.send_chat_message(message).add_done_callback(
                functools.partial(self.on_chat_message_sent, message)
            )

    def _on_draw_callback(self, future):
        log.info(future.result())
        tones.beep(2000, 200)

    def on_chat_message_sent(self, message, future):
        try:
            response = future.result()
            if response.entity.content["ok"]:
                self.parent.chat_list.add_item(f"You said {message}")
        except:
            log.exception("Failed to send chat message.")
            queueHandler.queueFunction(
                queueHandler.eventQueue, ui.message, "Failed to send chat message"
            )


class InternetChessboard(UserDrivenChessboard):
    """A board for playing internet chess."""

    cell_class = InternetChessboardCell

    def __init__(self, *args, client, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = client(board=self)
        self.prospective = self.prospective if self.prospective is not None else True
        self._is_game_started = False
        self.chat_list = SimpleList(parent=self, name="Chat", close_gesture="kb:f5")
        self.dialog.SetTitle("Starting Game...")

    def is_busy(self, index):
        if not self._is_game_started:
            return True
        return super().is_busy(index)

    def user_play(self, from_index, to_index):
        self.client.send_move(chess.Move(from_index, to_index)).add_done_callback(
            lambda future: self._execute_user_move(from_index, to_index, future)
        )

    def _execute_user_move(self, from_index, to_index, future):
        try:
            future.result()
            super(InternetChessboard, self).user_play(from_index, to_index)
        except:
            speak_next(
                speech.commands.WaveFileCommand(GameSound.error.filename),
                speech.commands.BreakCommand(100),
                _("Failed to send move"),
            )

    def restore_move_history(self, past_moves):
        for uci_move in past_moves:
            move = chess.Move.from_uci(uci_move)
            self.move_piece_and_check_game_status(move)

    def execute(self, event):
        func_name = f"on_{event.__member_name__}"
        callback = getattr(self, func_name, None)
        if callback is not None:
            wx.CallAfter(callback, event)

    def on_game_started(self, event):
        self._is_game_started = True
        info = event.info
        self.prospective = info.user_color
        self.dialog.SetTitle(
            _("{white} ({white_rating}) versus {black} ({black_rating})").format(
                white=info.white_username,
                black=info.black_username,
                white_rating=info.white_rating,
                black_rating=info.black_rating,
            )
        )
        self.dialog.set_time_control(info.time_control, True)

    def on_game_checkmate(self, event):
        print(f"Checkmate: winner is {event.winner}")

    def on_game_draw(self):
        self.game_drawn()

    def on_game_time_forfeit(self, event):
        self.game_time_forfeit(event.loser)

    def on_game_resign(self, event):
        self.game_resigned(event)

    def on_game_abort(self, event):
        color_name = self.game_anouncer.color_name(event.loser)
        self.game_error(f"{color_name} aborted the game")
        GameSound.error.play()

    def on_game_error(self, event):
        self.game_error()
        GameSound.error.play()

    def on_move_made(self, event):
        if event.player != self.prospective:
            self.move_piece_and_check_game_status(event.move)

    def on_draw_offered(self, event):
        self.handle_draw_offer()

    def respond_to_draw_offer(self, accepted: bool):
        self.client.handle_draw_offer(accepted)

    def on_chat_message_recieved(self, event):
        full_message = f"{event.from_whom} says {event.message}"
        self.chat_list.add_item(full_message)
        GameSound.chat.play()
        queueHandler.queueFunction(queueHandler.eventQueue, ui.message, full_message)

    def on_clock_tick(self, event):
        self.time_control = event.time_control
