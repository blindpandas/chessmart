from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lichess_client.utils.enums import VariantTypes


class AbstractTournaments(ABC):
    """An abstract class for Tournaments API Endpoint"""

    @abstractmethod
    def get_current(self):
        """Get recently finished, ongoing, and upcoming tournaments."""
        pass

    @abstractmethod
    def create(
        self,
        clock_time: int,
        clock_increment: int,
        minutes: int,
        name: str,
        wait_minutes: int,
        start_date: int,
        variant: "VariantTypes",
        rated: bool,
        position: str,
        berserk: bool,
        password: str,
        team_id: str,
        min_rating: int,
        max_rating: int,
        number_of_rated_games: int,
    ):
        """Create a public or private tournament to your taste."""
        pass

    @abstractmethod
    def export_games(self, tournament_id: str):
        """Download games of a tournament."""
        pass

    @abstractmethod
    def get_results(self, tournament_id: str, limit: int = 10):
        """Players of a tournament, with their score and performance, sorted by rank (best first)."""
        pass

    @abstractmethod
    def get_tournaments_created_by_a_user(self, username: str, limit: int = 10):
        """Get all tournaments created by a given user."""
        pass
