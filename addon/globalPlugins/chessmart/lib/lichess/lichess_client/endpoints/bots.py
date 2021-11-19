from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_bots import AbstractBots
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import BOTS_STREAM_INCOMING_EVENTS

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Bots(AbstractBots):
    """Class for Bots API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def stream_incoming_events(self) -> "Response":
        """
        Stream the events reaching a lichess user in real time.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.bots.get_my_profile()
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET, url=BOTS_STREAM_INCOMING_EVENTS, headers=headers
        )
        return response
