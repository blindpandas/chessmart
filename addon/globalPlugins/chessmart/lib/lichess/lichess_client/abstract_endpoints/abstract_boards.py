from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lichess_client.utils.enums import VariantTypes, ColorType, RoomTypes


class AbstractBoards(ABC):
    """An abstract class for Bots API Endpoint"""

    @abstractmethod
    def stream_incoming_events(self):
        """
        Stream the events reaching a lichess user in real time.
        """
        pass

    @abstractmethod
    def create_a_seek(
        self,
        time: int,
        increment: int,
        variant: "VariantTypes",
        color: "ColorType",
        rated: bool,
        rating_range,
    ):
        """
        Create a public seek, to start a game with a random player.
        """
        pass

    @abstractmethod
    def stream_game_state(self, game_id: str):
        """
        Stream the state of a game being played with the Board API
        """
        pass

    @abstractmethod
    def make_move(self, game_id: str, move: str, draw: bool):
        """Make a move in a game being played with the Board API."""
        pass

    @abstractmethod
    def abort_game(self, game_id: str):
        """Abort a game being played with the Board API."""
        pass

    @abstractmethod
    def resign_game(self, game_id: str):
        """Resign a game being played with the Board API."""
        pass

    @abstractmethod
    def write_in_chat(self, game_id: str, room: "RoomTypes", message: str):
        """Post a message to the player or spectator chat, in a game being played with the Board API."""
        pass

    @abstractmethod
    def handle_draw(self, game_id: str, accept: bool = True):
        """Create/accept/decline draw offers."""
        pass
