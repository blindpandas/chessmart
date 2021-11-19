import json
from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_tournaments import AbstractTournaments
from lichess_client.utils.enums import RequestMethods, VariantTypes
from lichess_client.utils.hrefs import (
    TOURNAMENTS_CURRENT,
    TOURNAMENTS_CREATE,
    TOURNAMENTS_EXPORT_GAMES,
    TOURNAMENTS_EXPORT_RESULTS,
    TOURNAMENTS_GET_CREATED_BY_USER,
)

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient
    from lichess_client.helpers import Response

__all__ = ["Tournaments"]


class Tournaments(AbstractTournaments):
    """Class for Tournaments API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client

    async def get_current(self):
        """
        Get recently finished, ongoing, and upcoming tournaments.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.tournaments.get_current()
        """

        headers = {"Content-Type": "application/json"}

        response = await self._client.request(
            method=RequestMethods.GET, url=TOURNAMENTS_CURRENT, headers=headers
        )
        return response

    async def create(
        self,
        clock_time: int,
        clock_increment: int,
        minutes: int,
        name: str = None,
        wait_minutes: int = 5,
        start_date: int = None,
        variant: "VariantTypes" = VariantTypes.STANDARD,
        rated: bool = True,
        position: str = None,
        berserk: bool = True,
        password: str = None,
        team_id: str = None,
        min_rating: int = None,
        max_rating: int = None,
        number_of_rated_games: int = None,
    ) -> "Response":
        """
        Create a public or private tournament to your taste.
            This endpoint mirrors the form on https://lichess.org/tournament/new.
            You can create up to 2 tournaments per day.

        Parameters
        ----------
        name: str, optional

        clock_time: int, required
            [0..60] Clock initial time in minutes

        clock_increment: int, required
            [0..60] Clock increment in seconds

        minutes: int, required
            [0..360] How long the tournament lasts, in minutes.

        wait_minutes: int, optional
            Default: 5
            How long to wait before starting the tournament, from now, in minutes

        start_date: int, optional
            Timestamp to start the tournament at a given date and time. Overrides the waitMinutes setting.

        variant: VariantTypes, optional
            Default: "standard"
            Enum: "standard" "chess960" "crazyhouse" "antichess" "atomic" "horde"
                "kingOfTheHill" "racingKings" "threeCheck"
            The variant to use in tournament games

        rated: bool, optional
            Default: true
            Games are rated and impact players ratings

        position: str, optional
            Default: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            Custom initial position (in FEN) for all games of the tournament. Must be one of
                https://github.com/ornicar/scalachess/blob/ab61b7e6d8d4ab602f6366b29b0e5715717e8944/src/main/scala/StartingPosition.scala#L25

        berserk: bool, optional
            Default: true
            Whether the players can use berserk

        password: str, optional
            Make the tournament private, and restrict access with a password

        team_id, str, optional
            Restrict entry to members of a team. The team_id is the last part of a team URL, e.g.
                https://lichess.org/team/coders has teamId = coders.
            Leave as None to let everyone join the tournament.

        min_rating: int, optional
            Minimum rating to join. Leave empty to let everyone join the tournament.

        max_rating: int, optional
            Maximum rating to join. Based on best rating reached in the last 7 days.
            Leave empty to let everyone join the tournament.

        number_of_rated_games: int, optional
            Minimum number of rated games required to join.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = await client.tournaments.create(clock_time=1, clock_increment=1, minutes=60)
        """

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "clockTime": clock_time,
            "clockIncrement": clock_increment,
            "minutes": minutes,
            "waitMinutes": wait_minutes,
            "variant": variant.value if isinstance(variant, VariantTypes) else variant,
            "rated": json.dumps(rated),
            "berserkable": json.dumps(berserk),
        }

        if name is not None:
            data["name"] = name

        if start_date is not None:
            data["startDate"] = start_date

        if position is None:
            data[
                "position"
            ] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

        if password is not None:
            data["password"] = password

        if team_id is not None:
            data["conditions.teamMember.teamId"] = team_id

        if min_rating is not None:
            data["conditions.minRating.rating"] = min_rating

        if max_rating is not None:
            data["conditions.maxRating.rating"] = max_rating

        if number_of_rated_games is not None:
            data["conditions.nbRatedGame.nb"] = number_of_rated_games

        response = await self._client.request(
            method=RequestMethods.POST,
            url=TOURNAMENTS_CREATE,
            data=data,
            headers=headers,
        )
        return response

    async def export_games(self, tournament_id: str) -> "Response":
        """
        Download games of a tournament. Games are sorted by reverse chronological order (most recent first)

        Parameters
        ----------
        tournament_id: str, required
            ID of the tournament to export.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.tournaments.export_games(tournament_id='q7zvsdUF')
        """

        headers = {"Content-Type": "application/json"}

        parameters = {
            "moves": "true",
            "pgnInJson": "false",
            "tags": "true",
            "clocks": "true",
            "evals": "true",
            "opening": "true",
        }

        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=TOURNAMENTS_EXPORT_GAMES.format(id=tournament_id),
            headers=headers,
            params=parameters,
        )
        return response

    async def get_results(self, tournament_id: str, limit: int = 10) -> "Response":
        """
        Players of a tournament, with their score and performance, sorted by rank (best first).
         games of a tournament. Games are sorted by reverse chronological order (most recent first)

        Parameters
        ----------
        tournament_id: str, required
            ID of the tournament to export.

        limit: int, optional
            Default: 10
            Max number of players to fetch

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.tournaments.get_results(tournament_id='q7zvsdUF')
        """

        headers = {"Content-Type": "application/json"}
        parameters = {"nb": limit}
        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=TOURNAMENTS_EXPORT_RESULTS.format(id=tournament_id),
            headers=headers,
            params=parameters,
        )
        return response

    async def get_tournaments_created_by_a_user(
        self, username: str, limit: int = 10
    ) -> "Response":
        """
        Get all tournaments created by a given user.
            Tournaments are sorted by reverse chronological order of start date (last starting first).

        Parameters
        ----------
        username: str, required

        limit: int, optional
            Default: 10
            Max number of tournaments to fetch.

        Returns
        -------
        Response object with response content.

        Example
        -------
        >>> from lichess_client import APIClient
        >>> client = APIClient(token='...')
        >>> response = client.tournaments.get_tournaments_created_by_a_user(username='amasend')
        """

        headers = {"Content-Type": "application/json"}

        parameters = {"nb": limit}
        response = await self._client.request_stream(
            method=RequestMethods.GET,
            url=TOURNAMENTS_GET_CREATED_BY_USER.format(username=username),
            headers=headers,
            params=parameters,
        )
        return response
