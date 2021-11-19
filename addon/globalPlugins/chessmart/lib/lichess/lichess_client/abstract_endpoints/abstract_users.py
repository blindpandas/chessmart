from abc import ABC, abstractmethod
from typing import List

from lichess_client.utils.enums import VariantTypes


class AbstractUsers(ABC):
    """An abstract class for Users API Endpoint"""

    @abstractmethod
    def get_real_time_users_status(self, users_ids: List[str]):
        """
        Read the online, playing and streaming flags of several users.

        This API is very fast and cheap on lichess side. So you can call it quite often (like once every 5 seconds).

        Use it to track players and know when they're connected on lichess and playing games."""
        pass

    @abstractmethod
    def get_all_top_10(self):
        """Get the top 10 players for each speed and variant."""
        pass

    @abstractmethod
    def get_one_leaderboard(self, variant: "VariantTypes", limit: int = 10):
        """
        Get the leaderboard for a single speed or variant (a.k.a. perfType).
            There is no leaderboard for correspondence or puzzles.
        """
        pass

    @abstractmethod
    def get_user_public_data(self, username: str):
        """Read public data of a user."""
        pass

    @abstractmethod
    def get_rating_history_of_a_user(self, username: str):
        """Read rating history of a user, for all perf types. There is at most one entry per day.
        Format of an entry is [year, month, day, rating]. month starts at zero (January)."""
        pass

    @abstractmethod
    def get_user_activity(self, username: str):
        """Read data to generate the activity feed of a user."""
        pass

    @abstractmethod
    def get_your_puzzle_activity(self, limit: int = None):
        """Download your puzzle activity in ndjson format.
        Puzzle activity is sorted by reverse chronological order (most recent first)"""
        pass

    @abstractmethod
    def get_users_by_id(self, users_ids: List[str]):
        """Get several users by their IDs. Users are returned in the order same order as the IDs.
        The method is POST so a longer list of IDs can be sent in the request body."""
        pass

    @abstractmethod
    def get_members_of_a_team(self, team_id: str):
        """Download your puzzle activity in ndjson format.
        Puzzle activity is sorted by reverse chronological order (most recent first)"""
        pass

    @abstractmethod
    def get_live_streamers(self):
        """Get basic info about currently streaming users."""
        pass
