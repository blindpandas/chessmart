from abc import ABC, abstractmethod


class AbstractTeams(ABC):
    """An abstract class for Teams API Endpoint"""

    @abstractmethod
    def get_members_of_a_team(self):
        """Not implemented"""
        pass

    @abstractmethod
    def join_a_team(self, team_id: str):
        """Join a team."""
        pass

    @abstractmethod
    def leave_a_team(self, team_id: str):
        """Leave a team."""
        pass

    @abstractmethod
    def kick_a_user_from_your_team(self, team_id: str, user_id: str):
        """Kick a member out of one of your teams."""
        pass
