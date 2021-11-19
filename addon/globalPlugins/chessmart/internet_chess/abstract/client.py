# coding: utf-8

import dataclasses
import wx
import functools
import contextlib
from abc import ABC, abstractmethod
from ...helpers import import_bundled
from ...game_elements import GameInfo
from ...time_control import ChessTimeControl


with import_bundled():
    import chess



@dataclasses.dataclass
class InternetGameInfo:
    white_username: str
    black_username: str
    time_control: ChessTimeControl
    user_color: chess.Color
    white_rating: int
    black_rating: int


class InternetChessAPIClient(ABC):
    """Represents an internet chess client."""

    def __init__(self, game_info: GameInfo):
        self.game_info = game_info

    def close(self):
        self.disconnect()

    @abstractmethod
    def connect(self):
        """
        Connect to the server, handling any authentication.
        Raise AuthenticationError when the provided credentials are invalid.
        """

    @abstractmethod
    def disconnect(self):
        """Disconnect the client."""

    @abstractmethod
    def create_challenge(self, opponent_username: str, **kwargs):
        """Create a challenge with a specific user."""

    @abstractmethod
    def seek_game(self, **kwargs):
        """Request to play a game."""

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass


class InternetChessBoardClient(ABC):
    """Represents events related to a single game."""

    def __init__(self, board):
        self.board = board

    @abstractmethod
    def abort_game(self):
        """abort the current game."""

    @abstractmethod
    def offer_draw(self):
        """Offer a draw in an on going game."""

    @abstractmethod
    def handle_draw_offer(self, accept):
        """Handle a draw offer from the opponent."""

    @abstractmethod
    def resign_game(self):
        """Resign a game."""

    @abstractmethod
    def send_chat_message(self, msg):
        """Send a chat message to your apponent."""

    @abstractmethod
    def send_move(self, move, draw=False):
        """Send a move to an on going game."""
