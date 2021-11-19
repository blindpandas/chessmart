# coding: utf-8

import typing as t
import os
import dataclasses
from ..helpers import import_bundled, LIB_DIRECTORY


with import_bundled():
    import chess


with import_bundled(os.path.join(LIB_DIRECTORY, "sqlite")):
    import sqlite3


PUZZLE_DATABASE_FILE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "lichess.puzzles.pop.sqlite"
)


@dataclasses.dataclass
class Puzzle:
    fen: str
    auto_performed_move: chess.Move
    solution_moves: t.Tuple[chess.Move]
    cat_name: str = None
    cat_description: str = None


def get_a_random_puzzle() -> Puzzle:
    with sqlite3.connect(PUZZLE_DATABASE_FILE) as con:
        row = con.execute("SELECT * FROM puzzle LIMIT 1").fetchone()
        auto_move, *solution_moves = [
            chess.Move.from_uci(uci_move)
            for uci_move in row[1].strip().split()
        ]
        return Puzzle(
            fen=row[0],
            auto_performed_move=auto_move,
            solution_moves=solution_moves,
        )
