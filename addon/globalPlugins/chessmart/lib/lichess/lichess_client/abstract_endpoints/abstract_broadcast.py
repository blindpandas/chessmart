from abc import ABC, abstractmethod


class AbstractBroadcast(ABC):
    """An abstract class for Broadcast API Endpoint"""

    @abstractmethod
    def create(
        self,
        name: str,
        description: str,
        source_url: str = None,
        markdown: str = None,
        credit: str = None,
        start_time: int = None,
    ):
        """Create a new broadcast to relay external games."""
        pass

    @abstractmethod
    def get(self, broadcast_id: str):
        """Get information about a broadcast that you created."""
        pass

    @abstractmethod
    def update(
        self,
        broadcast_id: str,
        name: str,
        description: str,
        source_url: str = None,
        markdown: str = None,
        credit: str = None,
        start_time: int = None,
    ):
        """Update information about a broadcast that you created."""
        pass

    @abstractmethod
    def push_pgn(self, broadcast_id: str, games: str):
        """Update your broadcast with new PGN."""
        pass
