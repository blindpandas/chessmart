# coding: utf-8

import threading
import typing as t
from functools import wraps
from logHandler import log
from .helpers import import_bundled


with import_bundled():
    import asyncio
    from concurrent.futures import ThreadPoolExecutor


THREADED_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="chessmart")
ASYNCIO_EVENT_LOOP = asyncio.new_event_loop()
ASYNCIO_LOOP_THREAD = None


def start_asyncio_event_loop():
    global ASYNCIO_LOOP_THREAD, ASYNCIO_EVENT_LOOP
    if ASYNCIO_LOOP_THREAD:
        return

    def _thread_target():
        log.info("Starting asyncio event loop")
        asyncio.set_event_loop(ASYNCIO_EVENT_LOOP)
        ASYNCIO_EVENT_LOOP.run_forever()

    ASYNCIO_LOOP_THREAD = threading.Thread(target=_thread_target, daemon=True, name="chessmart.asyncio.thread")
    ASYNCIO_LOOP_THREAD.start()


def terminate():
    global THREADED_EXECUTOR, ASYNCIO_LOOP_THREAD, ASYNCIO_EVENT_LOOP
    log.info("Shutting down the thread pool executor")
    THREADED_EXECUTOR.shutdown()
    if ASYNCIO_LOOP_THREAD:
        log.info("Shutting down asyncio event loop")
        ASYNCIO_EVENT_LOOP.call_soon_threadsafe(ASYNCIO_EVENT_LOOP.stop)


def asyncio_coroutine_to_concurrent_future(func):
    """Returns a concurrent.futures.Future that wrapps the decorated async function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run_coroutine_threadsafe(func(*args, **kwargs), ASYNCIO_EVENT_LOOP)

    return wrapper


def call_threaded(func: t.Callable[..., None]) -> t.Callable[..., "Future"]:
    """Call `func` in a separate thread. It wraps the function
    in another function that returns a `concurrent.futures.Future`
    object when called.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return THREADED_EXECUTOR.submit(func, *args, **kwargs)
        except RuntimeError:
            log.debug(
                f"Failed to submit function {func}."
            )

    return wrapper
