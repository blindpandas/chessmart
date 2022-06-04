# coding: utf-8


import os
from ..helpers import import_bundled, LIB_DIRECTORY


with import_bundled():
    import chess


with import_bundled(os.path.join(LIB_DIRECTORY, "sqlite")):
    import apsw
    from peewee import *
    from playhouse.apsw_ext import APSWDatabase


PUZZLE_DATABASE_FILE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    "lichess.puzzles.mini.sqlite"
)
database = APSWDatabase(PUZZLE_DATABASE_FILE, flags=apsw.SQLITE_ACCESS_EXISTS | apsw.SQLITE_ACCESS_READ)


class BaseModel(Model):
    class Meta:
        database = database


class Puzzle(BaseModel):
    fen = CharField()
    moves = CharField()
    popularity = IntegerField()
    rating = IntegerField()

    class Meta:
        table_name = "puzzle"

    @classmethod
    def get_total_count(cls):
        return cls.select().count()


class Theme(BaseModel):
    description = CharField()
    label = CharField()
    slug = CharField(index=True)

    def __repr__(self):
        return f"Theme(slug='{self.slug}', description='{self.description}')"

    class Meta:
        table_name = "theme"


class PuzzleTheme(BaseModel):
    puzzle = ForeignKeyField(column_name="puzzle_id", field="id", model=Puzzle, backref="themes")
    theme = ForeignKeyField(column_name="theme_id", field="id", model=Theme, backref="puzzles")

    class Meta:
        table_name = "puzzle_theme"
        indexes = ((("puzzle", "theme"), True),)
        primary_key = CompositeKey("puzzle", "theme")

