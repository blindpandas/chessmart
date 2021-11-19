from abc import ABC, abstractmethod


class AbstractSimulations(ABC):
    """An abstract class for Simulations API Endpoint"""

    @abstractmethod
    def get_current(self):
        """Get recently finished, ongoing, and upcoming simuls."""
        pass
