import json
from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_challenges import AbstractChallenges
from lichess_client.utils.enums import ColorType, VariantTypes, RequestMethods
from lichess_client.utils.hrefs import (
    CHALLENGES_CREATE,
    CHALLENGES_ACCEPT,
    CHALLENGES_DECLINE,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response

__all__ = ["Challenges"]


class Challenges(AbstractChallenges):
    """Class for Challenges API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def stream_incoming_events(self):
        """
        Stream the events reaching a lichess user in real time.
        This method is implemented in "boards" endpoint.

        See also
        --------
        lichess_client.APIClient.boards.stream_incoming_events()
        """
        raise NotImplementedError(
            'This method is implemented in "boards" endpoint.'
            "Please see: lichess_client.APIClient.boards.stream_incoming_events()"
        )

    async def create(
        self,
        username: str,
        time_limit: int = None,
        time_increment: int = None,
        rated: bool = False,
        days: int = None,
        color: "ColorType" = ColorType.RANDOM,
        variant: "VariantTypes" = VariantTypes.STANDARD,
        position: str = None,
    ) -> "Response":
        """
        Challenge someone to play. The targeted player can choose to accept or decline.
            If the challenge is accepted, you will be notified on the event stream that a new game has started.
            The game ID will be the same as the challenge ID.

        Parameters
        ----------
        username: str, required

        time_limit: int, optional
            [1..10800] Clock initial time in seconds. If empty, a correspondence game is created.

        time_increment: int, optional
            [0..60] Clock increment in seconds. If empty, a correspondence game is created.

        rated: bool: optional
            Game is rated and impacts players ratings

        days: int, optional
            [1..15] Days per move, for correspondence games. Time settings must be omitted.

        color: ColorType, optional
            Enum: "random" "white" "black"
            Which color you get to play, default: "random".

        variant: VariantTypes, optional
            Default: "standard"
            Enum: "standard" "chess960" "crazyhouse" "antichess" "atomic" "horde" "kingOfTheHill"
                    "racingKings" "threeCheck"
            The variant of the game

        position: str, optional
            Default: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            Custom initial position (in FEN). Variant must be standard, and the game cannot be rated.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.challenges.create(username="amasend")
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "rated": json.dumps(rated),
            "color": color.value if isinstance(color, ColorType) else color,
            "variant": variant.value if isinstance(variant, VariantTypes) else variant,
        }
        if time_limit is not None:
            data["clock.limit"] = time_limit

        if time_increment is not None:
            data["clock.increment"] = time_increment

        if days is not None and time_limit is None and time_increment is None:
            data["days"] = days

        if position is not None:
            data["position"] = position

        response = await self._client.request(
            method=RequestMethods.POST,
            url=CHALLENGES_CREATE.format(username=username),
            data=data,
            headers=headers,
        )
        return response

    async def accept(self, challenge_id: str) -> "Response":
        """
        Accept an incoming challenge.
            You should receive a gameStart event on the incoming events stream.

        Parameters
        ----------
        challenge_id: str, required
            ID of the challenge to accept, further game_id will be the same as this challenge_id.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.challenges.accept(challenge_id="5IrD6Gzz")
        """

        headers = {"Content-Type": "application/json"}

        response = await self._client.request(
            method=RequestMethods.POST,
            url=CHALLENGES_ACCEPT.format(challengeId=challenge_id),
            headers=headers,
        )
        return response

    async def decline(self, challenge_id: str) -> "Response":
        """
        Decline an incoming challenge.

        Parameters
        ----------
        challenge_id: str, required
            ID of the challenge to decline.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.challenges.decline(challenge_id="5IrD6Gzz")
        """

        headers = {"Content-Type": "application/json"}

        response = await self._client.request(
            method=RequestMethods.POST,
            url=CHALLENGES_DECLINE.format(challengeId=challenge_id),
            headers=headers,
        )
        return response
