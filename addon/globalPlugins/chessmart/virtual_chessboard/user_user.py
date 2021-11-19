# coding: utf-8

import tones
import queueHandler
import speech.commands
from ..helpers import import_bundled
from ..signals import game_started_signal
from .user_driven import UserDrivenChessboard


class UserUserChessboard(UserDrivenChessboard):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        game_started_signal.send(self)

    @property
    def prospective(self):
        return self.board.turn

    @prospective.setter
    def prospective(self, value):
        pass

    def move_piece_and_check_game_status(self, move, pre_speech=(), post_speech=()):
        post_speech = list(post_speech)
        if self.draw_offered:
            post_speech.extend(
                [
                    speech.commands.BreakCommand(500),
                    speech.commands.CallbackCommand(
                        lambda: queueHandler.queueFunction(
                            queueHandler.eventQueue, self.make_opponent_draw_offer
                        )
                    ),
                ]
            )
            self.draw_offered = False
        if self.board.turn is self.prospective:
            post_speech.append(
                speech.commands.CallbackCommand(
                    lambda: eventHandler.queueEvent("gainFocus", self)
                )
            )
        return super().move_piece_and_check_game_status(
            move, pre_speech, post_speech=post_speech
        )

