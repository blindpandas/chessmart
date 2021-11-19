import json
from typing import TYPE_CHECKING, List

from lichess_client.abstract_endpoints.abstract_boards import AbstractBoards
from lichess_client.utils.enums import (
    RequestMethods,
    VariantTypes,
    ColorType,
    RoomTypes,
)
from lichess_client.utils.client_errors import RatingRangeError
from lichess_client.utils.hrefs import (
    BOARDS_STREAM_INCOMING_EVENTS,
    BOARDS_CREATE_A_SEEK,
    BOARDS_STREAM_GAME_STATE,
    BOARDS_MAKE_MOVE,
    BOARDS_ABORT_GAME,
    BOARDS_RESIGN_GAME,
    BOARDS_WRITE_IN_CHAT,
    BOARDS_HANDLE_DRAW,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response

__all__ = ["Boards"]


class Boards(AbstractBoards):
    """Class for Boards API Endpoint"""

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
        >>> async for response in client.boards.stream_incoming_events():
        >>>     print(response)
        """
        headers = {"Content-Type": "application/json"}
        async for response in self._client.request_constant_stream(
            method=RequestMethods.GET,
            url=BOARDS_STREAM_INCOMING_EVENTS,
            headers=headers,
        ):
            yield response

    async def create_a_seek(
        self,
        time: int,
        increment: int,
        variant: "VariantTypes" = VariantTypes.STANDARD,
        color: "ColorType" = ColorType.RANDOM,
        rated: bool = False,
        rating_range: List[int] = None,
    ) -> "Response":
        """
        Create a public seek, to start a game with a random player.

        Parameters
        ----------
        rated: bool, optional
            Whether the game is rated and impacts players ratings.

        time: int, required
            Clock initial time in minutes.

        increment: int, required
            Clock increment in seconds.

        variant: VariantTypes, optional
             Enum: "standard" "chess960" "crazyhouse" "antichess" "atomic" "horde" "kingOfTheHill"
                "racingKings" "threeCheck"
                The variant of the game.

        color: ColorType, optional
             Enum: "random" "white" "black"
                The color to play. Better left empty to automatically get 50% white

        rating_range: List[int, int], optional
            The rating range of potential opponents. Better left empty. Example: [1500, 1800]

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.boards.create_a_seek(time=10, increment=0)
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "rated": json.dumps(rated),
            "time": time,
            "increment": increment,
            "variant": variant.value,
            "color": color.value,
        }
        if rating_range is not None and len(rating_range) != 2:
            raise RatingRangeError(
                "create_a_seek", reason="rating_range should contain only two numbers"
            )

        elif rating_range is not None:
            rating_range = [str(entry) for entry in rating_range]
            data["ratingRange"] = "-".join(rating_range)

        response = await self._client.request_stream(
            method=RequestMethods.POST,
            url=BOARDS_CREATE_A_SEEK,
            data=data,
            headers=headers,
        )
        return response

    async def stream_game_state(self, game_id: str) -> "Response":
        """
        Stream the state of a game being played with the Board API

        Parameters
        ----------
        game_id: str, required
            ID of the current playing game.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> async for response in client.boards.stream_game_state(game_id='5IrD6Gzz'):
        >>>     print(response)
        """
        headers = {"Content-Type": "application/json"}
        async for response in self._client.request_constant_stream(
            method=RequestMethods.GET,
            url=BOARDS_STREAM_GAME_STATE.format(gameId=game_id),
            headers=headers,
        ):
            yield response

    async def make_move(
        self, game_id: str, move: str, draw: bool = False
    ) -> "Response":
        """
        Make a move in a game being played with the Board API.
        The move can also contain a draw offer/agreement.


        Parameters
        ----------
        game_id: str, required
            ID of the current playing game.

        move: str, required
            Move in UCI format.

        draw: bool, optional
            Offer or accept a draw.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.boards.make_move(game_id='5IrD6Gzz', move='e2e4')
        """

        headers = {"Content-Type": "application/json"}
        parameters = {"offeringDraw": json.dumps(draw)}

        response = await self._client.request(
            method=RequestMethods.POST,
            url=BOARDS_MAKE_MOVE.format(gameId=game_id, move=move),
            params=parameters,
            headers=headers,
        )
        return response

    async def abort_game(self, game_id: str) -> "Response":
        """
        Abort a game being played with the Board API.

        Parameters
        ----------
        game_id: str, required
            ID of the current playing game.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.boards.abort_game(game_id='5IrD6Gzz')
        """

        response = await self._client.request(
            method=RequestMethods.POST, url=BOARDS_ABORT_GAME.format(gameId=game_id)
        )
        return response

    async def resign_game(self, game_id: str) -> "Response":
        """
        Resign a game being played with the Board API.

        Parameters
        ----------
        game_id: str, required
            ID of the current playing game.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.boards.resign_game(game_id='5IrD6Gzz')
        """

        response = await self._client.request(
            method=RequestMethods.POST, url=BOARDS_RESIGN_GAME.format(gameId=game_id)
        )
        return response

    async def write_in_chat(
        self, game_id: str, message: str, room: "RoomTypes" = RoomTypes.PLAYER
    ):
        """
        Post a message to the player or spectator chat, in a game being played with the Board API.

        Parameters
        ----------
        game_id: str, required
            ID of the current playing game.

        room: RoomTypes, optional
            Room where to post a message [player, spectator].

        message: str, required
            User message to post.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response_1 = await client.boards.write_in_chat(game_id='5IrD6Gzz', message="Hello!")
        >>> response_2 = await client.boards.write_in_chat(game_id='5IrD6Gzz', message="Hi all!", room=RoomTypes.SPECTATOR)
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "room": room.value if isinstance(room, RoomTypes) else room,
            "text": message,
        }

        response = await self._client.request(
            method=RequestMethods.POST,
            url=BOARDS_WRITE_IN_CHAT.format(gameId=game_id),
            data=data,
            headers=headers,
        )
        return response

    async def handle_draw(self, game_id: str, accept: bool = True) -> "Response":
        """
        Create/accept/decline draw offers.

        Parameters
        ----------
        game_id: str, required
            ID of the current playing game.

        accept: bool, optional
            True: Offer a draw, or accept the opponent's draw offer.
            False: Decline a draw offer from the opponent.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.boards.handle_draw(game_id='5IrD6Gzz', accept=True)
        """

        response = await self._client.request(
            method=RequestMethods.POST,
            url=BOARDS_HANDLE_DRAW.format(
                gameId=game_id, accept="yes" if accept else "no"
            ),
        )
        return response
