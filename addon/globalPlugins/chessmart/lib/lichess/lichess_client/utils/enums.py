from enum import Enum


class RequestMethods(Enum):
    """HTTP REST methods types"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class StatusTypes(str, Enum):
    """API response statuses"""

    SUCCESS = "success"
    ERROR = "error"


class VariantTypes(str, Enum):
    """Game variant types"""

    STANDARD = "standard"
    ULTRA_BULLET = "ultraBullet"
    BULLET = "bullet"
    BLITZ = "blitz"
    RAPID = "rapid"
    CLASSICAL = "classical"
    CHESS960 = "chess960"
    CRAZYHOUSE = "crazyhouse"
    ANTICHESS = "antichess"
    ATOMIC = "atomic"
    HORDE = "horde"
    KING_OF_THE_HILL = "kingOfTheHill"
    RACING_KINGS = "racingKings"
    THRESS_CHECK = "threeCheck"


class ColorType(str, Enum):
    """Color of the user pawns."""

    WHITE = "white"
    BLACK = "black"
    RANDOM = "random"


class RoomTypes(str, Enum):
    """Room types to posting user message."""

    PLAYER = "player"
    SPECTATOR = "spectator"


class SideTypes(Enum):
    """Side enum for Game description"""

    WHITE = 1
    BLACK = -1


# TODO: check more statuses
class GameStatusTypes(str, Enum):
    """Game status"""

    RESIGN = "resign"
    STARTED = "started"
