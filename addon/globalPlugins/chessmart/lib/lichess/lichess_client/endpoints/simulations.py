from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_simulations import AbstractSimulations
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import SIMULATIONS_GET

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Simulations(AbstractSimulations):
    """Class for Simulations API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def get_current(self) -> "Response":
        """
        Get recently finished, ongoing, and upcoming simuls.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.simulations.get_current()
        """

        response = await self._client.request(
            method=RequestMethods.GET, url=SIMULATIONS_GET
        )
        return response
