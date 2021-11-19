from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_messaging import AbstractMessaging
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import MESSAGES_SEND

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Messaging(AbstractMessaging):
    """Class for Messaging API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def send(self, username: str, text: str) -> "Response":
        """
        Send a private message to another player.

        Parameters
        ----------
        username: str, required

        text: str, required

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.messaging.send()
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {"text": text}

        response = await self._client.request(
            method=RequestMethods.POST,
            url=MESSAGES_SEND.format(username=username),
            data=data,
            headers=headers,
        )
        return response
