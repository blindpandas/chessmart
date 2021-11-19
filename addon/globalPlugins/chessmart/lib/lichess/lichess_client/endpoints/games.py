import json
from typing import TYPE_CHECKING, Union, List

from lichess_client.utils.enums import RequestMethods, VariantTypes, ColorType
from lichess_client.abstract_endpoints.abstract_games import AbstractGames
from lichess_client.helpers import Response
from lichess_client.utils.hrefs import (
    GAMES_EXPORT_ONE_URL,
    GAMES_EXPORT_USER_URL,
    GAMES_EXPORT_IDS_URL,
    GAMES_STREAM_CURRENT_URL,
    GAMES_ONGOING_URL,
    GAMES_CURRENT_TV_URL,
)
from lichess_client.utils.client_errors import ToManyIDs, LimitError

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient


class Games(AbstractGames):
    """Class for Games API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def export_one_game(self, game_id: str) -> "Response":
        """
        Download one game. Only finished games can be downloaded.

        Parameters
        ----------
        game_id: str, required
            ID of the game.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.export_one_game(game_id='q7zvsdUF')
        # TODO: add more examples
        """
        headers = {"Content-Type": "application/json"}
        parameters = {
            "moves": "true",
            "pgnInJson": "false",
            "tags": "true",
            "clocks": "true",
            "evals": "true",
            "opening": "true",
            "literate": "true",
        }
        response = await self._client.request(
            method=RequestMethods.GET,
            url=GAMES_EXPORT_ONE_URL.format(gameId=game_id),
            headers=headers,
            params=parameters,
        )
        return response

    async def export_games_of_a_user(
        self,
        username: str,
        since: int = None,
        until: int = None,
        limit: int = None,
        vs: str = None,
        rated: bool = None,
        variant: Union["VariantTypes", List["VariantTypes"]] = None,
        color: "ColorType" = None,
        analysed: bool = None,
        ongoing: bool = False,
    ) -> "Response":
        """
        Download all games of any user in PGN format.
        Games are sorted by reverse chronological order (most recent first)
        We recommend streaming the response, for it can be very long. https://lichess.org/@/german11 for instance has more than 320,000 games.
        The game stream is throttled, depending on who is making the request:
            Anonymous request: 15 games per second
            OAuth2 authenticated request: 25 games per second
            Authenticated, downloading your own games: 50 games per second

        Parameters
        ----------
        username: str, required
            Name of the user.

        since: int, optional
            Default: "Account creation date"
            Download games played since this timestamp.

        until: int, optional
            Default: "Now"
            Download games played until this timestamp.

        limit: int, optional
            Default: None
            How many games to download. Leave empty to download all games.

        vs: str, optional
            [Filter] Only games played against this opponent

        rated: bool, optional
             Default: None
            [Filter] Only rated (true) or casual (false) games

        variant: Union[VariantTypes, List[VariantTypes]], optional
            Default: None
            [Filter] Only games in these speeds or variants.
            Multiple variants can be specified in a list.

        color: ColorType, optional
            Default: None
            [Filter] Only games played as this color.

        analysed: bool, optional
            [Filter] Only games with or without a computer analysis available.

        ongoing: bool, optional
            Default: false
            [Filter] Also include ongoing games

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.export_games_of_a_user(username='amasend')
        # TODO: add more examples
        """
        if isinstance(variant, list):
            variant = ",".join([entry.value for entry in variant])
        elif isinstance(variant, VariantTypes):
            variant = variant.value

        headers = {"Content-Type": "application/json"}
        parameters = {
            "since": "Account creation date" if since is None else since,
            "until": "Now" if until is None else until,
            "max": "null" if limit is None else limit,
            "rated": "null" if rated is None else rated,
            "perfType": "null" if variant is None else variant,
            "color": "null" if color is None else color.value,
            "analysed": "null" if analysed is None else analysed,
            "ongoing": json.dumps(ongoing),
            "moves": "true",
            "pgnInJson": "false",
            "tags": "true",
            "clocks": "true",
            "evals": "true",
            "opening": "true",
        }

        if vs is not None:
            parameters["vs"] = vs

        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=GAMES_EXPORT_USER_URL.format(username=username),
            headers=headers,
            params=parameters,
        )
        return response

    async def export_games_by_ids(self, game_ids: List[str]) -> "Response":
        """
        Download games by IDs.

        Games are sorted by reverse chronological order (most recent first)

        The method is POST so a longer list of IDs can be sent in the request body. At most 300 IDs can be submitted.


        Parameters
        ----------
        game_ids: List[str], required
            IDs of the games.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.export_games_by_ids(game_ids=['q7zvsdUF', 'ILwozzRZ'])
        """
        if len(game_ids) > 300:
            raise ToManyIDs(
                "export_games_by_ids",
                reason="Cannot fetch more than 300 games at once. Please specify less than 300 game IDs.",
            )

        headers = {"Content-Type": "text/plain"}
        parameters = {
            "moves": "true",
            "pgnInJson": "false",
            "tags": "true",
            "clocks": "true",
            "evals": "true",
            "opening": "true",
        }
        response = await self._client.request_stream(
            method=RequestMethods.POST,
            url=GAMES_EXPORT_IDS_URL,
            headers=headers,
            params=parameters,
            data=",".join(game_ids),
        )
        return response

    async def stream_current_games(self, users: List[str]) -> "Response":
        """
        Stream the games played between a list of users, in real time.
        Only games where both players are part of the list are included.
        Maximum number of users: 300.
        The method is POST so a longer list of IDs can be sent in the request body.

        Parameters
        ----------
        users: List[str], required
            User names.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.stream_current_games(users=['amasend', 'lovlas', 'chess-network'])
        """
        raise NotImplementedError("This method is not implemented yet.")
        if len(users) > 300:
            raise ToManyIDs(
                "stream_current_games",
                reason="Cannot fetch more than 300 games at once. Please specify less than 300 users.",
            )

        headers = {"Content-Type": "text/plain"}
        response = await self._client.request_stream(
            method=RequestMethods.POST,
            url=GAMES_STREAM_CURRENT_URL,
            headers=headers,
            data=",".join(users),
        )
        return response

    async def get_ongoing_games(self, limit: int = 9) -> "Response":
        """
        Get the ongoing games of the current user.
        Real-time and correspondence games are included. The most urgent games are listed first.

        Parameters
        ----------
        limit: int, optional
            Number of games to fetch, default is 9.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response_1 = client.users.get_ongoing_games(limit=10)
        >>> response_2 = client.users.get_ongoing_games()
        """
        if limit > 50:
            raise LimitError("get_ongoing_games", reason="Max number of games is 50.")
        elif limit < 1:
            raise LimitError("get_ongoing_games", reason="Min number of games is 1.")

        headers = {"Content-Type": "application/json"}
        parameters = {
            "nb": limit,
        }
        response = await self._client.request(
            method=RequestMethods.GET,
            url=GAMES_ONGOING_URL,
            headers=headers,
            params=parameters,
        )
        return response

    async def get_current_tv_games(self) -> "Response":
        """
        Get basic info about the best games being played for each speed and variant,
        but also computer games and bot games.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.users.get_current_tv_games()
        """
        headers = {"Content-Type": "application/json"}
        response = await self._client.request(
            method=RequestMethods.GET, url=GAMES_CURRENT_TV_URL, headers=headers
        )
        return response
