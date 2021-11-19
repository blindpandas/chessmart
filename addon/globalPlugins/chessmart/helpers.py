# coding: utf-8

# Copyright (c) 2021 Blind Pandas Team
# This file is covered by the GNU General Public License.

import sys
import os
import platform
import contextlib
import enum
import queueHandler
import speech
from nvwave import playWaveFile


PLUGIN_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
LIB_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "lib")
BIN_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "bin")
SOUNDS_DIRECTORY = os.path.join(PLUGIN_DIRECTORY, "sounds")


class GameSound(enum.Enum):
    black_square = "black_square"
    start_game = "start_game"
    chess_pieces = "chess_pieces"
    invalid = "invalid"
    request_promotion = "request_promotion"
    promotion = "promotion"
    capture = "capture"
    en_passant = "en_passant"
    check = "check"
    castling = "castling"
    pick_piece = "pick_piece"
    drop_piece = "drop_piece"
    drop_move = "drop_move"
    drop_target = "drop_target"
    game_over = "game_over"
    error = "error"
    resigned = "resigned"
    drawn = "drawn"
    time_pass = "time_pass"
    time_critical = "time_critical"
    time_forfeit = "time_forfeit"
    score_list_open = "score_list_open"
    score_list_close = "score_list_close"
    menu_open = "menu_open"
    chat = "chat"
    you_won = "you_won"
    puzzle_solved = "puzzle_solved"

    def __init__(self, filename):
        self.filename = os.path.join(SOUNDS_DIRECTORY, f"{filename}.wav")

    def play(self):
        playWaveFile(self.filename)


class Color(enum.Enum):
    Red = "#96D454"
    Blue = "#0000FF"
    Green = "#00B050"
    Yellow = "#FFFF00"
    Purple = "#953553"
    DarkGray = "#3C3C3C"


@contextlib.contextmanager
def import_bundled(packages_path=LIB_DIRECTORY):
    sys.path.insert(0, packages_path)
    try:
        yield
    finally:
        sys.path.remove(packages_path)


def is_64bit_windows() -> bool:
    return platform.machine().endswith("64")


def intersperse(lst, item):
    """Taken from: https://stackoverflow.com/a/5921708"""
    result = [item] * (len(lst) * 2 - 1)
    result[0::2] = lst
    return result


def speak_next(
    speech_sequence: speech.SpeechSequence, priority: speech.Spri = speech.Spri.NEXT
) -> None:
    speech.speak(speech_sequence, priority=priority)
