from typing import TYPE_CHECKING

from lichess_client.abstract_endpoints.abstract_chess_bot import AbstractChessBot

if TYPE_CHECKING:
    from lichess_client.clients.base_client import BaseClient


class ChessBot(AbstractChessBot):
    """Class for Chess Bot API Endpoint"""

    def __init__(self, client: "BaseClient") -> None:
        self._client = client
