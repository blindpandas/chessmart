# coding: utf-8


import typing as t
import os
import random
import dataclasses
import json
import globalVars
from .models import Puzzle, Theme, PuzzleTheme
from ..helpers import import_bundled


with import_bundled():
    import chess
    from cached_property import cached_property


@dataclasses.dataclass
class PuzzleInfo:
    puzzle_id: int
    rating: int
    fen: str
    auto_performed_move: chess.Move
    solution_moves: t.Tuple[chess.Move]
    themes: t.Tuple[Theme]

    @classmethod
    def from_database_puzzle(cls, puzzle: Puzzle):
        auto_performed_move, *solution_moves =(chess.Move.from_uci(m.strip()) for m in puzzle.moves.split())
        themes = tuple(
            t.theme
            for t in puzzle.themes.join(Theme).order_by(Theme.slug)
        )
        return cls(
            puzzle_id=puzzle.id,
            rating=puzzle.rating,
            fen=puzzle.fen,
            auto_performed_move=auto_performed_move,
            solution_moves=solution_moves,
            themes=themes
        )

    def get_theme_info(self):
        for theme in self.themes:
            yield theme.label, theme.description


@dataclasses.dataclass
class PuzzleSet:
    classifiers: t.Tuple[str] 
    current_item_index: int

    def __getitem__(self, index):
        return self.puzzles[index]

    def __iter__(self):
        return self

    def __next__(self):
        try:
            item = self[self.current_item_index]
            self.current_item_index += 1
            return item
        except IndexError:
            raise StopIteration

    @cached_property
    def puzzles(self):
        return [
            PuzzleInfo.from_database_puzzle(puzzle)
            for puzzle in (Puzzle
                .select()
                .join(PuzzleTheme)
                .join(Theme)
                .where(Theme.slug.in_(self.classifiers))
                .order_by(Puzzle.rating.asc())
                .limit(100)
            )
        ]

    def get_identifier(self):
        return ".".join(sorted(set(c for c in self.classifiers)))

    def get_history_filename(self):
        return os.path.join(
            globalVars.appArgs.configPath,
            ".chessmart.puzzle.history",
            self.get_identifier() + ".json"
        )

    def save_history(self):
        history_filename = self.get_history_filename()
        if not os.path.isdir(os.path.dirname(history_filename)):
            os.mkdir(os.path.dirname(history_filename))
        data = {
            "classifiers": self.classifiers,
            "current_item_index": self.current_item_index
        }
        with open(history_filename, "w") as file:
            json.dump(data, file)

    def load_history(self):
        history_file = self.get_history_filename()
        if not os.path.isfile(history_file):
            raise FileNotFoundError("Could not find the history file")
        with open(history_file, "r") as file:
            parsed = json.load(file)
        return PuzzleSet(
            classifiers=parsed["classifiers"],
            current_item_index=parsed["current_item_index"]
        )


@dataclasses.dataclass(init=False)
class RandomPuzzleSet(PuzzleSet):

    def __init__(self, num_puzzles=3):
        self.num_puzzles = num_puzzles
        self.classifiers = ()
        self.current_item_index = 0

    @cached_property
    def puzzles(self):
        choice_range = range(
            Puzzle.raw("SELECT MIN(puzzle.id) FROM puzzle;").get().id,
            Puzzle.raw("SELECT MAX(puzzle.id) FROM puzzle;").get().id,
        )
        chosen_ids = random.sample(choice_range, self.num_puzzles)
        return [
            PuzzleInfo.from_database_puzzle(puzzle)
            for puzzle in Puzzle.select().where(Puzzle.id.in_(chosen_ids))
        ]

    def save_history(self):
        pass

    def load_history(self):
        raise FileNotFoundError("NA")

