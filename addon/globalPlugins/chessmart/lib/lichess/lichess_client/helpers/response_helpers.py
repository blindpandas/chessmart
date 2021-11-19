from typing import List, Union, TYPE_CHECKING

from lichess_client.utils.enums import RequestMethods, StatusTypes

if TYPE_CHECKING:
    from chess.pgn import Game

__all__ = ["Response", "ResponseMetadata", "ResponseEntity"]


class BaseHelper:
    """Base Helper class with defined custom magic methods, also for to dictionary conversion."""

    def to_dict(self) -> dict:
        _dict: dict = {}
        for key, val in vars(self).items():
            if hasattr(val, "to_dict"):
                _dict[key] = val.to_dict()
            else:
                _dict[key] = val
        return _dict

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return str(self.to_dict())


class ResponseMetadata(BaseHelper):
    """Metadata class for the response object."""

    def __init__(
        self, method: str, url: str, content_type: str, timestamp: bytes
    ) -> None:
        self.method = RequestMethods[method]
        self.url = url
        self.content_type = content_type
        self.timestamp = timestamp


class ResponseEntity(BaseHelper):
    """Entity class for the response object."""

    def __init__(
        self,
        code: int,
        reason: str,
        status: "StatusTypes",
        content: Union[List[dict], dict, "Game"],
    ) -> None:
        self.code = code
        self.reason = reason
        self.status = status
        self.content = content


class Response(BaseHelper):
    """The Response class. Used to store every API response in the unified way."""

    def __init__(self, metadata: "ResponseMetadata", entity: "ResponseEntity") -> None:
        self.metadata = metadata
        self.entity = entity
