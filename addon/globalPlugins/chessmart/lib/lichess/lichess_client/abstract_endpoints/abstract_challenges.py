from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lichess_client.utils.enums import VariantTypes, ColorType


class AbstractChallenges(ABC):
    """An abstract class for Challenges API Endpoint"""

    @abstractmethod
    def stream_incoming_events(self):
        pass

    @abstractmethod
    def create(
        self,
        username: str,
        time_limit: int,
        time_increment: int,
        rated: bool,
        days: int,
        color: "ColorType",
        variant: "VariantTypes",
        position: str,
    ):
        """Challenge someone to play."""
        pass

    @abstractmethod
    def accept(self, challenge_id: str):
        """Accept an incoming challenge."""
        pass

    @abstractmethod
    def decline(self, challenge_id: str):
        """Decline an incoming challenge."""
        pass
