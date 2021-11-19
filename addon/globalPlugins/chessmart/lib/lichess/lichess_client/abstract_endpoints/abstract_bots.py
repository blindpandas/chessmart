from abc import ABC, abstractmethod


class AbstractBots(ABC):
    """An abstract class for Bots API Endpoint"""

    @abstractmethod
    def stream_incoming_events(self):
        """
        Stream the events reaching a lichess user in real time.
        """
        pass
