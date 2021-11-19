from lichess_client.clients.abstract_client import AbstractClient
from lichess_client.clients.base_client import BaseClient
from lichess_client.endpoints import (
    Account,
    Broadcast,
    Challenges,
    ChessBot,
    Games,
    Messaging,
    Relations,
    Simulations,
    Studies,
    Teams,
    Tournaments,
    Users,
    Bots,
    Boards,
)


class APIClient(AbstractClient):
    """
    ASYNC APIClient class for handling secure connections with Lichees API via token usage.

    Parameters
    ----------
    token: str, required
        String with token provided from Lichees.org account site.

    loop: asyncio event loop, optional
        Asyncio event loop for async mode operations
    """

    def __init__(self, token: str, loop=None) -> None:
        self._client = BaseClient(token=token, loop=loop)

        self.account = Account(client=self._client)
        self.broadcast = Broadcast(client=self._client)
        self.challenges = Challenges(client=self._client)
        self.chess_bot = ChessBot(client=self._client)
        self.games = Games(client=self._client)
        self.messaging = Messaging(client=self._client)
        self.relations = Relations(client=self._client)
        self.simulations = Simulations(client=self._client)
        self.studies = Studies(client=self._client)
        self.teams = Teams(client=self._client)
        self.tournaments = Tournaments(client=self._client)
        self.users = Users(client=self._client)
        self.bots = Bots(client=self._client)
        self.boards = Boards(client=self._client)
