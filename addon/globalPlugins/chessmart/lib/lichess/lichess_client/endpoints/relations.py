from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_relations import AbstractRelations
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import RELATIONS_FOLLOWERS_URL, RELATIONS_FOLLOWING_URL

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Relations(AbstractRelations):
    """Class for Relations API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def get_users_followed_by_a_user(self, username: str) -> "Response":
        """
        Fetching all users followed by current user.
            This is a streaming endpoint.

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
        >>> response = client.users.get_users_followed_by_a_user(username='amasend')
        """
        headers = {
            "Content-Type": "application/x-ndjson",
        }
        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=RELATIONS_FOLLOWING_URL.format(username=username),
            headers=headers,
        )
        return response

    async def get_users_who_follow_a_user(self, username: str) -> "Response":
        """
        Fetching all users who follow this user.
            This is a streaming endpoint.

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
        >>> response = client.users.get_users_who_follow_a_user(username='amasend')
        """
        headers = {
            "Content-Type": "application/x-ndjson",
        }
        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=RELATIONS_FOLLOWERS_URL.format(username=username),
            headers=headers,
        )
        return response
