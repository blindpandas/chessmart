# coding: utf-8

import tones
import dataclasses
import typing as t
import queueHandler
import ui
import speech
from scriptHandler import script
from ..helpers import import_bundled
from .base import BaseVirtualChessboard, BaseChessboardCell


with import_bundled():
    import chess
    import chess.pgn


@dataclasses.dataclass
class PGNGameInfo:
    result: str
    white: str
    black: str
    date: str
    event: str
    site: str
    termination: t.Optional[str]
    filename: str
    offset: t.Optional[int] = 0

    @classmethod
    def args_from_headers(cls, headers):
        return dict(
            result=cls.parse_pgn_result_string(headers.get("Result", "")),
            white=headers.get("White", "?"),
            black=headers.get("Black", "?"),
            date=headers.get("Date", "????.??.??"),
            event=headers.get("Date", "?"),
            site=headers.get("Date", "?"),
            termination=headers.get("Termination"),
        )

    @classmethod
    def game_info_from_pgn_filename(cls, filename):
        with open(filename, "r", encoding="utf-8") as file:
            while True:
                offset = file.tell()
                headers = chess.pgn.read_headers(file)
                if headers is None:
                    break
                yield cls(
                    filename=filename, offset=offset, **cls.args_from_headers(headers)
                )

    @property
    def description(self):
        return " ".join(
            [
                f"{self.white} versus {self.black},",
                f"{self.event},",
                f" - {self.date}",
            ]
        )

    @staticmethod
    def parse_pgn_result_string(result_string):
        if result_string.strip() == "*":
            return "Game not finished"
        w_score, b_score = [s.strip() for s in result_string.strip().split("-")]
        if w_score == "1":
            return "White Won"
        elif b_score == "1":
            return "Black won"
        elif w_score == b_score == "1/2":
            return "Game ended in a draw"
        raise ValueError(f"Cannot parse PGN result {result_string}")


@dataclasses.dataclass
class PGNGame:
    game_obj: chess.pgn.Game
    moves: t.Tuple[chess.Move]
    info: PGNGameInfo

    @classmethod
    def from_game_info(cls, info):
        with open(info.filename, "r", encoding="utf-8") as file:
            file.seek(info.offset)
            game = chess.pgn.read_game(file)
            return cls(
                game_obj=game, moves=tuple(g.move for g in game.mainline()), info=info
            )

    def get_board(self):
        return self.game_obj.board()


class PGNChessboardCell(BaseChessboardCell):
    @script(gesture="kb:backspace")
    def script_backspace(self, gesture):
        self.parent.rewind()


class PGNPlayerChessboard(BaseVirtualChessboard):
    cell_class = PGNChessboardCell

    def __init__(self, *args, **kwargs):
        game = kwargs.pop("game")
        super().__init__(*args, **kwargs)
        self.game = game
        self.board = self.game.get_board()
        self.current_move = -1
        # GUI Stuff
        info = self.game.info
        self.dialog.SetTitle(
            f"{info.white} versus {info.black} " f"{info.date} " f"{info.event} "
        )

    def activate_cell(self, index):
        self.fast_forward()

    def move_piece_and_check_game_status(self, move, pre_speech=(), post_speech=()):
        post_speech = list(post_speech) + [
            speech.commands.BreakCommand(150),
            speech.commands.CallbackCommand(
                lambda: queueHandler.queueFunction(
                    queueHandler.eventQueue, self.set_focus_to_cell, move.to_square
                )
            ),
        ]
        super().move_piece_and_check_game_status(
            move, pre_speech, post_speech=post_speech
        )

    def fast_forward(self):
        next_move = self.current_move + 1
        if next_move < len(self.game.moves):
            self.move_piece_and_check_game_status(self.game.moves[next_move])
            self.current_move = next_move
        else:
            if self.game.info.termination is not None:
                message = f"The game has been terminated because of: {self.game.info.termination}"
            else:
                message = self.game.info.result
            queueHandler.queueFunction(queueHandler.eventQueue, ui.message, message)

    def rewind(self):
        return
