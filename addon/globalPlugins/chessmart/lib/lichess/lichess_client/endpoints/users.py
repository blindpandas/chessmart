from typing import List, TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_users import AbstractUsers
from lichess_client.utils.enums import RequestMethods, VariantTypes
from lichess_client.utils.hrefs import (
    USERS_ACTIVITY_URL,
    USERS_GET_BY_IDS_URL,
    USERS_LIVE_STREAMERS_URL,
    USERS_MY_PUZZLE_ACTIVITY_URL,
    USERS_PLAYER_TOP_URL,
    USERS_PLAYER_URL,
    USERS_RATING_HISTORY_URL,
    USERS_STATUS_URL,
    USERS_TEAM_MEMBERS_URL,
    USERS_USER_PUBLIC_DATA_URL,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Users(AbstractUsers):
    """Class for Users API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def get_real_time_users_status(self, users_ids: List[str]) -> "Response":
        """
        Read the online, playing and streaming flags of several users.

        This API is very fast and cheap on lichess side. So you can call it quite often (like once every 5 seconds).

        Use it to track players and know when they're connected on lichess and playing games.

        Parameters
        ----------
        users_ids: List[str], required
            List of the users IDs to fetch information about the status.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_real_time_users_status(
        >>>     users_ids=['amasend', 'aliquantus','chess-network', 'lovlas'])
        """
        headers = {"Content-Type": "application/json"}
        parameters = {"ids": ",".join(users_ids)}
        response = await self._client.request(
            method=RequestMethods.GET,
            url=USERS_STATUS_URL,
            headers=headers,
            params=parameters,
        )
        return response

    async def get_all_top_10(self) -> "Response":
        """
        Get the top 10 players for each speed and variant.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_all_top_10()
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.lichess.v3+json",
        }
        response = await self._client.request(
            method=RequestMethods.GET, url=USERS_PLAYER_URL, headers=headers
        )
        return response

    async def get_one_leaderboard(
        self, variant: "VariantTypes", limit: int = 10
    ) -> "Response":
        """
        Get the leaderboard for a single speed or variant (a.k.a. perfType).
            There is no leaderboard for correspondence or puzzles.

        Parameters
        ----------
        limit: int, optional
            How many users to fetch.

        variant: VariantTypes, required


        Returns
        -------
        Response object with response content.

        See also
        --------
        VariantTypes

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_one_leaderboard(variant=VariantTypes.BLITZ)
        >>> response_2 = client.users.get_one_leaderboard(variant=VariantTypes.ANTICHESS, limit=100)
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.lichess.v3+json",
        }
        response = await self._client.request(
            method=RequestMethods.GET,
            url=USERS_PLAYER_TOP_URL.format(nb=limit, perfType=variant),
            headers=headers,
        )
        return response

    async def get_user_public_data(self, username: str) -> "Response":
        """
        Read public data of a user.

        Parameters
        ----------
        username: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_user_public_data(username='amasend')
        """
        headers = {
            "Content-Type": "application/json",
        }
        response = await self._client.request(
            method=RequestMethods.GET,
            url=USERS_USER_PUBLIC_DATA_URL.format(username=username),
            headers=headers,
        )
        return response

    async def get_rating_history_of_a_user(self, username: str) -> "Response":
        """
        Read rating history of a user, for all perf types. There is at most one entry per day.
            Format of an entry is [year, month, day, rating]. month starts at zero (January).

        Parameters
        ----------
        username: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_rating_history_of_a_user(username='amasend')
        """
        # TODO: Make an ISSUE, endpoint supports 'Content-Type': 'text/html' not 'application/json'
        headers = {
            "Content-Type": "text/html",
        }
        response = await self._client.request(
            method=RequestMethods.GET,
            url=USERS_RATING_HISTORY_URL.format(username=username),
            headers=headers,
        )
        return response

    async def get_user_activity(self, username: str) -> "Response":
        """
        Read data to generate the activity feed of a user.

        Parameters
        ----------
        username: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_user_activity(username='amasend')
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET,
            url=USERS_ACTIVITY_URL.format(username=username),
            headers=headers,
        )
        return response

    async def get_your_puzzle_activity(self, limit: int = None) -> "Response":
        """
        Download your puzzle activity in ndjson format.
        Puzzle activity is sorted by reverse chronological order (most recent first)

        Parameters
        ----------
        limit: int, optional
            Hom many records to fetch, if None, all records will be fetched (by streaming).

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_your_puzzle_activity()
        >>> response_2 = client.users.get_your_puzzle_activity(limit=50)
        """
        headers = {
            "Content-Type": "application/x-ndjson",
        }
        parameters = {"max": limit if limit is not None else "null"}
        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=USERS_MY_PUZZLE_ACTIVITY_URL,
            headers=headers,
            params=parameters,
        )
        return response

    async def get_users_by_id(self, users_ids: List[str]) -> "Response":
        """
        Get several users by their IDs. Users are returned in the order same order as the IDs.
            The method is POST so a longer list of IDs can be sent in the request body.

        Parameters
        ----------
        users_ids: List[str], required
            List of the users IDs to fetch information about the status.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_users_by_id(users_ids=['amasend', 'aliquantus','chess-network', 'lovlas'])
        """
        headers = {"Content-Type": "text/plain"}
        data = ",".join(users_ids)
        response = await self._client.request(
            method=RequestMethods.POST,
            url=USERS_GET_BY_IDS_URL,
            headers=headers,
            data=data,
        )
        return response

    async def get_members_of_a_team(self, team_id: str) -> "Response":
        """
        Download your puzzle activity in ndjson format.
            Puzzle activity is sorted by reverse chronological order (most recent first)

        Parameters
        ----------
        team_id: str, required
            Team ID

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_members_of_a_team(team_id='team')
        """
        headers = {
            "Content-Type": "application/x-ndjson",
        }
        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=USERS_TEAM_MEMBERS_URL.format(teamId=team_id),
            headers=headers,
        )
        return response

    async def get_live_streamers(self) -> "Response":
        """
        Get basic info about currently streaming users.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_live_streamers()
        """
        headers = {
            "Content-Type": "application/json",
        }
        response = await self._client.request(
            method=RequestMethods.GET, url=USERS_LIVE_STREAMERS_URL, headers=headers
        )
        return response
