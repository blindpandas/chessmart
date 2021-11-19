from abc import ABC, abstractmethod


class AbstractMessaging(ABC):
    """An abstract class for Messaging API Endpoint"""

    @abstractmethod
    def send(self, username: str, text: str):
        """Send a private message to another player."""
        pass
