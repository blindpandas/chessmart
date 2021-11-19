from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_teams import AbstractTeams
from lichess_client.helpers import Response
from lichess_client.utils.hrefs import (
    TEAMS_JOIN_URL,
    TEAMS_LEAVE_URL,
    TEAMS_KICK_USER_URL,
)
from lichess_client.utils.enums import RequestMethods

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient


class Teams(AbstractTeams):
    """Class for Teams API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def get_members_of_a_team(self) -> None:
        """Not implemented

        See also
        --------
        client.users.get_members_of_a_team(...)
        """
        raise NotImplementedError("Please use client.users.get_members_of_a_team(...)")

    async def join_a_team(self, team_id: str) -> "Response":
        """
        Join a team. If the team join policy requires a confirmation, and the team owner is not the oAuth app owner,
        then the call fails with 403 Forbidden.

        Parameters
        ----------
        team_id: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.join_a_team(team_id = 'some_team')
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.POST,
            url=TEAMS_JOIN_URL.format(teamId=team_id),
            headers=headers,
        )
        return response

    async def leave_a_team(self, team_id: str) -> "Response":
        """
        Leave a team.

        Parameters
        ----------
        team_id: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.leave_a_team(team_id = 'some_team')
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.POST,
            url=TEAMS_LEAVE_URL.format(teamId=team_id),
            headers=headers,
        )
        return response

    async def kick_a_user_from_your_team(
        self, team_id: str, user_id: str
    ) -> "Response":
        """
        Kick a member out of one of your teams.

        Parameters
        ----------
        team_id: str, required

        user_id: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.kick_a_user_from_your_team(team_id='some_team', user_id='amasend')
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.POST,
            url=TEAMS_KICK_USER_URL.format(teamId=team_id, userId=user_id),
            headers=headers,
        )
        return response
