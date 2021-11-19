from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_broadcast import AbstractBroadcast
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import (
    BROADCASTS_CREATE,
    BROADCASTS_GET,
    BROADCASTS_PUSH_PGN,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Broadcast(AbstractBroadcast):
    """Class for Broadcast API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def create(
        self,
        name: str,
        description: str,
        source_url: str = None,
        markdown: str = None,
        credit: str = None,
        start_time: int = None,
    ) -> "Response":
        """
        Create a new broadcast to relay external games.

        Parameters
        ----------
        name: str, required
            Name of the broadcast. Length must be between 3 and 80 characters.

        description: str, required
            Short description of the broadcast. Length must be between 3 and 400 characters.

        source_url: str, optional
            URL that Lichess will poll to get updates about the games. It must be publicly accessible from the Internet.
            Example: http://myserver.org/myevent/round-10/games.pgn
            If the syncUrl is missing, then the broadcast needs to be fed by pushing PGN to it.

        markdown: str, optional
            Optional long description of the broadcast.
            Markdown is supported. Length must be less than 20,000 characters.

        credit: str, optional
            Optional short text to give credit to the source provider.

        start_time: int, optional
            Timestamp of broadcast start. Leave empty to manually start the broadcast.
            Example: 1356998400070

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.broadcast.create(name="my broadcast", description="this is my broadcast...")
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"name": name, "description": description}

        if source_url is not None:
            data["syncUrl"] = source_url

        if markdown is not None:
            data["markdown"] = markdown

        if credit is not None:
            data["credit"] = credit

        if start_time is not None:
            data["startsAt"] = start_time

        response = await self._client.request(
            method=RequestMethods.POST,
            url=BROADCASTS_CREATE,
            data=data,
            headers=headers,
        )
        return response

    async def get(self, broadcast_id: str) -> "Response":
        """
        Get information about a broadcast that you created. You will need it if you want to update that broadcast.

        Parameters
        ----------
        broadcast_id: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.broadcast.get(broadcast_id="wje07860")
        """

        headers = {"Content-Type": "application/json"}

        response = await self._client.request(
            method=RequestMethods.GET,
            url=BROADCASTS_GET.format(broadcastId=broadcast_id),
            headers=headers,
        )
        return response

    async def update(
        self,
        broadcast_id: str,
        name: str,
        description: str,
        source_url: str = None,
        markdown: str = None,
        credit: str = None,
        start_time: int = None,
    ) -> "Response":
        """
        Update information about a broadcast that you created.
        This endpoint accepts the same form data as the web form.
        All fields must be populated with data. Missing fields will override the broadcast with empty data.
        For instance, if you omit startDate, then any pre-existing start date will be removed.

        Parameters
        ----------
        broadcast_id: str, required

        name: str, required
            Name of the broadcast. Length must be between 3 and 80 characters.

        description: str, required
            Short description of the broadcast. Length must be between 3 and 400 characters.

        source_url: str, optional
            URL that Lichess will poll to get updates about the games. It must be publicly accessible from the Internet.
            Example: http://myserver.org/myevent/round-10/games.pgn
            If the syncUrl is missing, then the broadcast needs to be fed by pushing PGN to it.

        markdown: str, optional
            Optional long description of the broadcast.
            Markdown is supported. Length must be less than 20,000 characters.

        credit: str, optional
            Optional short text to give credit to the source provider.

        start_time: int, optional
            Timestamp of broadcast start. Leave empty to manually start the broadcast.
            Example: 1356998400070

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.broadcast.update(broadcast_id="wje07860", name="my broadcast", description="this is my updated broadcast...")
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"name": name, "description": description}

        if source_url is not None:
            data["syncUrl"] = source_url

        if markdown is not None:
            data["markdown"] = markdown

        if credit is not None:
            data["credit"] = credit

        if start_time is not None:
            data["startsAt"] = start_time

        response = await self._client.request(
            method=RequestMethods.POST,
            url=BROADCASTS_GET.format(broadcastId=broadcast_id),
            data=data,
            headers=headers,
        )
        return response

    async def push_pgn(self, broadcast_id: str, games: str) -> "Response":
        """
        Update your broadcast with new PGN. Only for broadcast without a source URL.

        Parameters
        ----------
        broadcast_id: str, required

        games: str, required
            The PGN. It can contain up to 64 games, separated by a double new line.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.broadcast.push_pgn(broadcast_id="wje07860", games="...")
        """

        response = await self._client.request(
            method=RequestMethods.POST,
            url=BROADCASTS_PUSH_PGN.format(broadcastId=broadcast_id),
            data=games,
        )
        return response
