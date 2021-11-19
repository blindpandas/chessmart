# coding: utf-8

import asyncio
import functools
import os
import dataclasses
import threading
import tones
import functools
import wx
from logHandler import log
from ..concurrency import ASYNCIO_EVENT_LOOP
from ..helpers import import_bundled, LIB_DIRECTORY
from ..signals import Chessboard_signals
from ..time_control import ChessTimeControl
from ..concurrency import asyncio_coroutine_to_concurrent_future
from .abstract.client import (
    InternetChessAPIClient,
    InternetChessBoardClient,
    InternetGameInfo,
)
from .abstract.exceptions import (
    InternetChessConnectionError,
    AuthenticationError,
    OperationTimeout,
    ChallengeRejected,
    ChallengedUserIsOffline,
)
from .abstract.events import InternetChessAPIEvent, InternetChessBoardEvent


with import_bundled():
    import asyncio
    import chess
    from opnieuw import retry_async


with import_bundled(os.path.join(LIB_DIRECTORY, "lichess")):
    import ndjson
    import lichess_client
    from lichess_client.utils.enums import ColorType, StatusTypes, RoomTypes
    from aiohttp.client_exceptions import ClientError, ClientConnectorError


PERSONAL_TOKEN = "lip_vU2uugFDpnfUj5ZHj6dF"
CONNECTION_RELATED_EXCEPTIONS = (
    ConnectionError,
    ClientConnectorError,
    ClientError,
    InternetChessConnectionError,
)
RETRIABLE_EXCEPTIONS = CONNECTION_RELATED_EXCEPTIONS + (OperationTimeout,)


def cast_exception_to_connection_error_if_appropriate(coro):
    """Cast the exception raised by the coro to InternetChessConnectionError if appropriate."""

    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except CONNECTION_RELATED_EXCEPTIONS as e:
            raise InternetChessConnectionError("Connection Failed") from e

    return wrapper


class LichessAPIClient(InternetChessAPIClient):
    """Client for lichess.org."""

    game_finished_signal = Chessboard_signals.signal("lichess.org.game.finished")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lichess = None
        self.current_challenge_id = None
        self._lichess_events_listener_task = None
        self.challenge_future = ASYNCIO_EVENT_LOOP.create_future()
        self.seek_future = ASYNCIO_EVENT_LOOP.create_future()

    async def connect(self):
        if self.lichess is None:
            self.lichess = lichess_client.APIClient(token=PERSONAL_TOKEN)
            self._lichess_events_listener_task = asyncio.create_task(
                self._start_listening_for_lichess_board_events()
            )

    def disconnect(self):
        ASYNCIO_EVENT_LOOP.call_soon_threadsafe(self._lichess_events_listener_task.cancel)

    @asyncio_coroutine_to_concurrent_future
    @cast_exception_to_connection_error_if_appropriate
    @retry_async(
        retry_on_exceptions=RETRIABLE_EXCEPTIONS,
        max_calls_total=3,
        retry_window_after_first_call_in_seconds=10,
    )
    async def create_challenge(
        self,
        opponent_username: str,
        rated: bool = False,
        timeout: float = 120,
    ):
        await self.connect()
        user_response = await self.lichess.users.get_real_time_users_status(
            users_ids=[opponent_username]
        )
        if not user_response.entity.content:
            raise ChallengedUserIsOffline(opponent_username)
        user_info = user_response.entity.content[0]
        if not user_info.get("online", False):
            raise ChallengedUserIsOffline(opponent_username)
        base_time, increment = self._get_time_control_info(self.game_info.time_control)
        response = await self.lichess.challenges.create(
            username=opponent_username,
            time_limit=base_time,
            time_increment=increment,
            rated=rated,
            color=chess.COLOR_NAMES[self.game_info.prospective],
        )
        if response.entity.code != 200:
            raise InternetChessConnectionError("Failed to connect to lichess.org")
        data = response.entity.content["challenge"]
        if data["status"] != "created":
            raise ChallengeRejected(None)
        game_id = data["id"]
        self.current_challenge_id = game_id
        try:
            return await asyncio.wait_for(self.challenge_future, timeout)
        except asyncio.TimeoutError:
            raise OperationTimeout(game_id)

    @asyncio_coroutine_to_concurrent_future
    @cast_exception_to_connection_error_if_appropriate
    @retry_async(
        retry_on_exceptions=RETRIABLE_EXCEPTIONS,
        max_calls_total=3,
        retry_window_after_first_call_in_seconds=10,
    )
    async def seek_game(
        self,
        rated: bool = False,
        timeout: float = 30,
    ):
        await self.connect()
        base_time, increment = self._get_time_control_info(self.game_info.time_control)
        response_data = await self.lichess.boards.create_a_seek(
            time=base_time / 60,
            increment=increment,
            rated=rated,
            color=ColorType(chess.COLOR_NAMES[self.game_info.prospective]),
        )
        try:
            return await asyncio.wait_for(self.seek_future, timeout)
        except asyncio.TimeoutError:
            raise OperationTimeout("Failed to seek game")

    @retry_async(
        retry_on_exceptions=RETRIABLE_EXCEPTIONS,
        max_calls_total=3,
        retry_window_after_first_call_in_seconds=10,
    )
    async def _start_listening_for_lichess_board_events(self):
        async for response in self.lichess.boards.stream_incoming_events():
            try:
                self._process_raw_lichess_event(response.entity.content)
                asyncio.sleep(0.2)
            except Exception as e:
                log.info(f"Failed to listen: {e}")
                raise e

    def _process_raw_lichess_event(self, data):
        log.info(f"Received a lichess API event: {data}.")
        event_info = ndjson.loads(data)[0]
        evt_type = event_info["type"]
        if evt_type == "gameStart":
            asyncio.sleep(1)
            game_id = event_info["game"]["id"]
            board_client = functools.partial(
                LichessBoardClient, game_id=game_id, client=self
            )
            if game_id == self.current_challenge_id:
                self.current_challenge_id = None
                self.challenge_future.set_result(board_client)
            elif not self.seek_future.done():
                self.seek_future.set_result(board_client)
        elif evt_type == "gameFinish":
            game_id = event_info["game"]["id"]
            if game_id == self.current_challenge_id:
                self.current_challenge_id = None
                if not self.challenge_future.done():
                    self.challenge_future.set_exception(ChallengeRejected(game_id))
            self.game_finished_signal.send(game_id)
        elif evt_type == "challengeDeclined":
            game_id = event_info["challenge"]["id"]
            if game_id == self.current_challenge_id:
                self.current_challenge_id = None
                if not self.challenge_future.done():
                    self.challenge_future.set_exception(ChallengeRejected(game_id))

    def _get_time_control_info(self, time_control):
        base_time, increment, *__ = time_control.astuple()
        return base_time, increment


class LichessBoardClient(InternetChessBoardClient):
    """Represent the lichess board API endpoint."""

    def __init__(self, *, game_id, client, board):
        self.game_id = game_id
        self.client = client
        self.board = board
        self.username = None
        self.ic_game_info = None
        # Just for convenience
        self.lichess = self.client.lichess
        self.listener_task = ASYNCIO_EVENT_LOOP.create_task(self.start_realtime_game_stream())
        self.client.game_finished_signal.connect(
            self.on_game_finish, sender=self.game_id
        )

    @retry_async(
        retry_on_exceptions=RETRIABLE_EXCEPTIONS,
        max_calls_total=10,
        retry_window_after_first_call_in_seconds=15,
    )
    async def start_realtime_game_stream(self):
        username_response = await self.lichess.account.get_my_profile()
        self.username = username_response.entity.content["username"]
        log.info(f"The username is {self.username}")
        async for response in self.client.lichess.boards.stream_game_state(
            game_id=self.game_id
        ):
            log.info(f"Received a game event: {response}")
            if response.entity.status is StatusTypes.ERROR:
                tones.beep(500, 500)
                await asyncio.sleep(5)
                self.start_realtime_game_stream()
                break
            try:
                tones.beep(100, 100)
                self._handle_realtime_game_stream_status(response.entity.content)
                asyncio.sleep(0.1)
            except Exception as e:
                log.exception(f"Failed to stream game events: {e}", exc_info=True)
                raise e

    def close(self):
        ASYNCIO_EVENT_LOOP.call_soon_threadsafe(self.listener_task.cancel)

    def on_game_finish(self, sender):
        self.close()
        self.board.game_over("Game Finished")

    @asyncio_coroutine_to_concurrent_future
    async def abort_game(self):
        return await self.lichess.boards.abort_game(game_id=self.current_game.game_id)

    @asyncio_coroutine_to_concurrent_future
    async def offer_draw(self):
        return await self.lichess.boards.handle_draw(
            game_id=self.game_id,
            accept=True,
        )

    @asyncio_coroutine_to_concurrent_future
    async def resign_game(self):
        return await self.lichess.boards.resign_game(game_id=self.game_id)

    @asyncio_coroutine_to_concurrent_future
    async def send_chat_message(self, message):
        return await self.lichess.boards.write_in_chat(
            game_id=self.game_id, message=message, room=RoomTypes.PLAYER
        )

    @asyncio_coroutine_to_concurrent_future
    async def send_move(self, move, draw=False):
        return await self.lichess.boards.make_move(
            game_id=self.game_id, move=move.uci(), draw=draw
        )

    @asyncio_coroutine_to_concurrent_future
    async def handle_draw_offer(self, accept):
        return await self.lichess.boards.handle_draw(
            game_id=self.game_id,
            accept=accept,
        )

    def _process_game_state_started(self, status, maybe_restore_state=False):
        moves = status["moves"].split()
        move_turn = bool(len(moves) % 2)
        if not moves:
            return
        if maybe_restore_state and moves:
            self.board.restore_move_history(moves[:-1])
        event = InternetChessBoardEvent.move_made(
            chess.Move.from_uci(moves[-1]), player=move_turn
        )
        self.board.execute(event)
        time_control = ChessTimeControl(
            white_base_time=status["wtime"] / 1000,
            white_increment=status["winc"] / 1000,
            black_base_time=status["btime"] / 1000,
            black_increment=status["binc"] / 1000,
        )
        clock_tick_event = InternetChessBoardEvent.clock_tick(time_control=time_control)
        self.board.execute(clock_tick_event)

    def _handle_realtime_game_stream_status(self, data):
        tones.beep(200, 100)
        status = ndjson.loads(data)[0]
        status_type = status["type"]
        if status_type == "gameState":
            if status["status"] == "started":
                self._process_game_state_started(status)
            elif status["status"] == "resign":
                winner = chess.WHITE if status["winner"] == "white" else chess.BLACK
                event = InternetChessBoardEvent.game_resigned(loser=not winner)
                self.board.execute(event)
            elif status["status"] == "outoftime":
                loser = chess.WHITE if status["winner"] == "black" else chess.BLACK
                time_forfeit_event = InternetChessBoardEvent.game_time_forfeit(
                    loser=loser
                )
                self.board.execute(time_forfeit_event)
        elif status_type == "gameFull":
            base_time, increment = (
                status["clock"]["initial"] / 1000,
                status["clock"]["increment"] / 1000,
            )
            time_control = ChessTimeControl.from_string(
                f"{int(base_time)};{int(increment)}"
            )
            info = InternetGameInfo(
                white_username=status["white"]["name"],
                black_username=status["black"]["name"],
                time_control=time_control,
                user_color=chess.WHITE
                if status["white"]["name"] == self.username
                else chess.BLACK,
                white_rating=status["white"]["rating"],
                black_rating=status["black"]["rating"],
            )
            self.ic_game_info = info
            start_game_event = InternetChessBoardEvent.game_started(info)
            self.board.execute(start_game_event)
            self._process_game_state_started(status["state"], maybe_restore_state=True)
        elif status_type == "chatLine":
            if status["username"] == self.username:
                return
            event = InternetChessBoardEvent.chat_message_recieved(
                from_whom=status["username"],
                message=status["text"],
            )
            self.board.execute(event)


"""
elif evt_type == "challenge":
            challenge_info = event_info["challenge"]
            challenger = challenge_info["challenger"]["name"]
            base_time, increment = challenge_info["timeControl"]["limit"], challenge_info["timeControl"]["increment"]
            time_control = ChessTimeControl.from_string(f"{base_time};{increment}")
            given_color = challenge_info["color"] == "random"
            if given_color == "random":
                color = None
            elif given_color == "white":
                color = chess.WHITE
            else:
                color = chess.BLACK
            self.current_challenge = LichessChallenge(
                game_id=challenge_info["id"],
                with_whom=challenger,
                user_color=color
            )
            event = ICEvent.challenge_recieved(
                from_whom=challenger,
                playing_as_color=color,
                time_control=time_control,
            )
            self.board.execute(event)
            """
