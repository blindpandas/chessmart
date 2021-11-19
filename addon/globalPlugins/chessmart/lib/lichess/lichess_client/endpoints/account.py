import json
from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_account import AbstractAccount
from lichess_client.utils.enums import RequestMethods
from lichess_client.utils.hrefs import (
    ACCOUNT_URL,
    ACCOUNT_EMAIL_URL,
    ACCOUNT_KID_URL,
    ACCOUNT_PREFERENCES_URL,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response


class Account(AbstractAccount):
    """Class for Account API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def get_my_profile(self) -> "Response":
        """
        Public information about the logged in user.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.account.get_my_profile()
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET, url=ACCOUNT_URL, headers=headers
        )
        return response

    async def get_my_email_address(self) -> "Response":
        """
        Read the email address of the logged in user.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.account.get_my_email_address()
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET, url=ACCOUNT_EMAIL_URL, headers=headers
        )
        return response

    async def get_my_preferences(self) -> "Response":
        """
        Read the preferences of the logged in user.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.account.get_my_preferences()
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET, url=ACCOUNT_PREFERENCES_URL, headers=headers
        )
        return response

    async def get_my_kid_mode_status(self) -> "Response":
        """
        Read the kid mode status of the logged in user.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.account.get_my_kid_mode_status()
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET, url=ACCOUNT_KID_URL, headers=headers
        )
        return response

    async def set_my_kid_mode_status(self, *, turned_on: bool) -> "Response":
        """
        Set the kid mode status of the logged in user.

        Parameters
        ----------
        turned_on: bool, required
            The indicator to turn on or turn off the kid mode.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.account.set_my_kid_mode_status()()
        """
        headers = {"Content-Type": "application/json"}
        parameters = {"v": json.dumps(turned_on)}
        response = await self._client.request(
            method=RequestMethods.POST,
            url=ACCOUNT_KID_URL,
            headers=headers,
            params=parameters,
        )
        return response
