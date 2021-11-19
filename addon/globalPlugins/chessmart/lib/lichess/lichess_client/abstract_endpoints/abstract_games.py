from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from lichess_client.utils.enums import VariantTypes, ColorType


class AbstractGames(ABC):
    """An abstract class for Games API Endpoint"""

    @abstractmethod
    def export_one_game(self, game_id: str):
        """Download one game. Only finished games can be downloaded."""
        pass

    @abstractmethod
    def export_games_of_a_user(
        self,
        username: str,
        since: int = None,
        until: int = None,
        max: int = None,
        vs: str = None,
        rated: bool = None,
        variant: "VariantTypes" = None,
        color: "ColorType" = None,
        analysed: bool = None,
        ongoing: bool = False,
    ):
        """Download all games of any user in PGN format."""
        pass

    @abstractmethod
    def export_games_by_ids(self, game_ids: List[str]):
        """Download games by IDs."""
        pass

    @abstractmethod
    def stream_current_games(self, users: List[str]):
        """Stream current games between users."""
        pass

    @abstractmethod
    def get_ongoing_games(self, limit: int = 9):
        """Get the ongoing games of the current user."""
        pass

    @abstractmethod
    def get_current_tv_games(self):
        """Get basic info about the best games being played for each speed and variant,
        but also computer games and bot games."""
        pass
