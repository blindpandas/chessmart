# coding: utf-8

"""Exceptions raised by remote internet chess servers."""


class InternetChessClientError(Exception):
    """The base exception of all internet client operations."""


class InternetChessConnectionError(InternetChessClientError, ConnectionError):
    """Raised when a network problem occurs."""


class AuthenticationError(InternetChessClientError):
    """Invalid credentials provided."""


class OperationTimeout(InternetChessClientError, TimeoutError):
    """Raised when an operation timeout."""

    def __init__(self, game_id):
        self.game_id = game_id


class ChallengedUserIsOffline(InternetChessClientError):
    """The user you're trying to challenge is offline."""

    def __init__(self, username):
        self.username = username


class ChallengeRejected(InternetChessClientError):
    """Raised when the challenge is rejected."""

    def __init__(self, game_id):
        self.game_id = game_id

