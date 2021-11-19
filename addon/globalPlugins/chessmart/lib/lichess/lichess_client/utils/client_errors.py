import logging
from typing import Any


logger = logging.getLogger("lichess_client")


class BaseError(Exception):
    def __init__(self, value: Any, reason: str) -> None:
        super().__init__(value, reason)
        logger.debug(f"Error in: {value} Reason: {reason}")


class ToManyIDs(BaseError):
    def __init__(self, value: Any, reason: str) -> None:
        super().__init__(value, reason)


class LimitError(BaseError):
    def __init__(self, value: Any, reason: str) -> None:
        super().__init__(value, reason)


class RatingRangeError(BaseError):
    def __init__(self, value: Any, reason: str) -> None:
        super().__init__(value, reason)
