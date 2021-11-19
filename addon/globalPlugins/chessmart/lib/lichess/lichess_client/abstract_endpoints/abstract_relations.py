from abc import ABC, abstractmethod


class AbstractRelations(ABC):
    """An abstract class for Relations API Endpoint"""

    @abstractmethod
    def get_users_followed_by_a_user(self, username: str):
        """Fetching all users followed by current user.
        This is a streaming endpoint."""
        pass

    @abstractmethod
    def get_users_who_follow_a_user(self, username: str):
        """Fetching all users who follow this user.
        This is a streaming endpoint."""
        pass
