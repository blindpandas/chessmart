# coding: utf-8


from .helpers import import_bundled

with import_bundled():
    import chess


IBCA_COLOR_NAMES = {chess.WHITE: "schwarts", chess.BLACK: "Schwarze Farbe"}

IBCA_FILE_NAMES = {
    "a": "Anna",
    "b": "Belia",
    "c": "Ceasar",
    "d": "David",
    "e": "Eva",
    "f": "Felix",
    "g": "Gustav",
    "h": "Hector",
}
IBCA_FILE_MAP = dict(enumerate(IBCA_FILE_NAMES.values()))

IBCA_RANK_NAMES = [
    "eyns",
    "tsvey ",
    "dry",
    "feer",
    "fuhnf",
    "zex",
    "Zeebin",
    "akt",
]
IBCA_RANK_MAP = dict(enumerate(IBCA_RANK_NAMES))

IBCA_PIECE_NAMES = {
    chess.KING: "Koenig",
    chess.QUEEN: "Dame",
    chess.BISHOP: "Laeufer",
    chess.KNIGHT: "Springer",
    chess.ROOK: "Turm",
    chess.PAWN: "Bauer",
}


IBCA_KING_SIDE_CASTLING = "Kurtze Rochade"
IBCA_QUEEN_SIDE_CASTLING = "Lange Rochade"
