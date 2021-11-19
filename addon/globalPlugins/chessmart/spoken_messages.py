# coding: utf-8


import abc
from .helpers import import_bundled
from .ibca_notation import (
    IBCA_COLOR_NAMES,
    IBCA_FILE_MAP,
    IBCA_RANK_MAP,
    IBCA_PIECE_NAMES,
    IBCA_KING_SIDE_CASTLING,
    IBCA_QUEEN_SIDE_CASTLING,
)


with import_bundled():
    import chess


class GameAnnouncer(abc.ABC):
    @abc.abstractmethod
    def piece_name(self, piece_type: chess.PieceType) -> str:
        """Return piece name given piece type."""

    @abc.abstractmethod
    def color_name(self, color: chess.Color) -> str:
        """Return the name of the given color."""

    @abc.abstractmethod
    def square_name(self, square: chess.Square) -> str:
        """Return the name of the given square index."""

    @abc.abstractmethod
    def square_file(self, square: chess.Square) -> str:
        """Return the name of the file of the given square."""

    @abc.abstractmethod
    def square_rank(self, square: chess.Square) -> str:
        """Return the rank of the file of the given square."""

    def describe_piece(self, piece: chess.Piece):
        """Return the color and the name of the piece in a single string."""
        return f"{self.color_name(piece.color)} {self.piece_name(piece.piece_type)}"

    @abc.abstractmethod
    def normal_move(
        self, move: chess.Move, moved_piece: chess.Piece, move_maker=chess.Color
    ) -> list:
        """Return a list of strings to describe the given move."""

    @abc.abstractmethod
    def capture_move(
        self, move: chess.Move, moved_piece: chess.Piece, captured: chess.Piece
    ) -> list:
        """Return a list of strings to describe a capture move."""

    @abc.abstractmethod
    def castling_move(self, move_maker: chess.Color, is_king_side: bool) -> list:
        """Return a list of strings to describe description a castling move."""

    @abc.abstractmethod
    def drop_move(self, move_maker: chess.Color, move: chess.Move):
        """A drop move."""

    @abc.abstractmethod
    def promotion_move(self, move: chess.Move, move_maker: chess.Color) -> list:
        """Return a list of string describing a promotion move."""


class StandardGameAnnouncer(GameAnnouncer):
    def piece_name(self, piece_type: chess.PieceType) -> str:
        return chess.piece_name(piece_type)

    def color_name(self, color: chess.Color) -> str:
        return chess.COLOR_NAMES[color]

    def square_name(self, square: chess.Square) -> str:
        return chess.square_name(square)

    def square_file(self, square: chess.Square) -> str:
        return chess.FILE_NAMES[chess.square_file(square)]

    def square_rank(self, square: chess.Square) -> str:
        return chess.RANK_NAMES[chess.square_rank(square)]

    def normal_move(
        self, move: chess.Move, moved_piece: chess.Piece, move_maker=chess.Color
    ) -> list:
        move_desc = [
            self.describe_piece(moved_piece),
            "to",
            self.square_name(move.to_square),
        ]
        if (moved_piece.piece_type is not chess.PAWN) and (move.from_square != move.to_square):
            move_desc.insert(1, f"from {self.square_name(move.from_square)}")
        return move_desc

    def capture_move(
        self, move: chess.Move, moved_piece: chess.Piece, captured: chess.Piece
    ) -> list:
        return [
            self.describe_piece(moved_piece),
            f"was at {self.square_name(move.from_square)}",
            "captured",
            self.describe_piece(captured),
            "at",
            self.square_name(move.to_square),
        ]

    def castling_move(self, move_maker: chess.Color, is_king_side: bool) -> list:
        return [
            self.color_name(move_maker),
            "castled",
            "king side" if is_king_side else "queen side",
        ]

    def drop_move(self, move_maker, move):
        return (
            self.color_name(move_maker),
            "dropped a ",
            self.piece_name(move.drop),
        )

    def promotion_move(self, move, move_maker):
        return [
            self.color_name(move_maker),
            f"Promoted {self.piece_name(chess.PAWN)}",
            "at",
            self.square_name(move.from_square),
            "to",
            f"a {self.piece_name(move.promotion)}",
            "at",
            self.square_name(move.to_square),
        ]


class IBCAGameAnnouncer(GameAnnouncer):
    def piece_name(self, piece_type: chess.PieceType) -> str:
        return IBCA_PIECE_NAMES[piece_type]

    def color_name(self, color: chess.Color) -> str:
        return IBCA_COLOR_NAMES[color]

    def square_name(self, square: chess.Square) -> str:
        return "{file} {rank}".format(
            file=IBCA_FILE_MAP[chess.square_file(square)],
            rank=IBCA_RANK_MAP[chess.square_rank(square)],
        )

    def square_file(self, square: chess.Square) -> str:
        return IBCA_FILE_MAP[chess.square_file(square)]

    def square_rank(self, square: chess.Square) -> str:
        return IBCA_RANK_MAP[chess.square_rank(square)]

    def normal_move(
        self, move: chess.Move, moved_piece: chess.Piece, move_maker=chess.Color
    ) -> list:
        return [self.describe_piece(moved_piece), self.square_name(move.to_square)]

    def capture_move(
        self, move: chess.Move, moved_piece: chess.Piece, captured: chess.Piece
    ) -> list:
        return [
            self.describe_piece(moved_piece),
            "captured",
            self.describe_piece(captured),
            "at",
            self.square_name(move.to_square),
        ]

    def castling_move(self, move_maker: chess.Color, is_king_side: bool) -> list:
        return [
            self.color_name(move_maker),
            IBCA_KING_SIDE_CASTLING if is_king_side else IBCA_QUEEN_SIDE_CASTLING,
        ]

    def drop_move(self, move_maker, move):
        return (
            self.color_name(move_maker),
            "dropped a ",
            self.piece_name(move.drop),
            "at ",
            self.square_name(move.to_square),
        )

    def promotion_move(self, move, move_maker):
        return [
            self.color_name(move_maker),
            f"Promoted {self.piece_name(chess.PAWN)}",
            "at",
            self.square_name(move.from_square),
            "to",
            f"a {self.piece_name(move.promotion)}",
            "at",
            self.square_name(move.to_square),
        ]


standard_game_announcer = StandardGameAnnouncer()
ibca_game_announcer = IBCAGameAnnouncer()
