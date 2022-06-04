# coding: utf-8

import sys
import functools
import wx
import globalPluginHandler
import gui
import globalVars
import ui
import tones
import queueHandler
import winUser
from scriptHandler import script
from .helpers import import_bundled

with import_bundled():
    # Import some packages  replacing NVDA builtin packages
    # with original packages obtained from a Python 3.7 installation
    # to fix some missing sub packages and modules
    if "http" in sys.modules:
        sys.modules.pop("http")
    import http

    if "xml" in sys.modules:
        sys.modules.pop("xml")
    import xml

    # Normal imports
    import chess

from . import concurrency
from .time_control import NULL_TIME_CONTROL
from .chessboard import ChessboardDialog
from .game_elements import GameInfo, ChessVariant
from .virtual_chessboard import (
    PGNGame,
    PGNGameInfo,
    PGNPlayerChessboard,
    UserUserChessboard,
    UserEngineChessboard,
    PuzzleChessboard,
)
from .graphical_interface.new_game_dialog import NewGameOptionsDialog
from .internet_chess import LichessAPIClient


class ChessboardMenu(wx.Menu):
    def __init__(self, global_plugin_object):
        super().__init__()
        # Start an asyncio event loop for running io tasks
        concurrency.start_asyncio_event_loop()
        self.global_plugin_object = global_plugin_object
        # Append the menu items
        new_game_item = self.Append(
            wx.ID_ANY, _("&New Game..."), _("Start a new chess game")
        )
        random_puzzle_item = self.Append(
            wx.ID_ANY, _("&Random Puzzle"), _("Play a random puzzle")
        )
        replay_pgn_file_item = self.Append(
            wx.ID_ANY,
            _("&Replay PGN File..."),
            _("Load an replay a portable game notation (.pgn) file"),
        )
        # Insert this menu in NVDA's menu
        self.itemHandle = gui.mainFrame.sysTrayIcon.menu.Insert(
            3,
            wx.ID_ANY,
            _("Chess&board"),
            self,
            _("Start a new chess game or re open an existing one"),
        )
        # Bind menu items to events
        self.Bind(wx.EVT_MENU, self.onNewGame, new_game_item)
        self.Bind(wx.EVT_MENU, self.onRandomPuzzle, random_puzzle_item)
        self.Bind(wx.EVT_MENU, self.onReplayPGN, replay_pgn_file_item)

    def onNewGame(self, event):
        dialog = NewGameOptionsDialog(gui.mainFrame, callback=self.create_new_game)
        gui.runScriptModalDialog(dialog)

    def create_new_game(self, vboard_cls, game_info):
        self.global_plugin_object.initialize_and_show_chessboard_dialog(vboard_cls, game_info)

    def onRandomPuzzle(self, event):
        from .puzzle_database import RandomPuzzleSet
        puzzles = RandomPuzzleSet()
        game_info = GameInfo(
            pychess_board=chess.Board(),
            variant=ChessVariant.STANDARD,
            time_control=NULL_TIME_CONTROL,
            prospective=None,
            vboard_kwargs=dict(puzzles=puzzles)
        )
        self.global_plugin_object.initialize_and_show_chessboard_dialog(
            PuzzleChessboard,
            game_info
        )

    def onReplayPGN(self, event):
        openFileDialog = wx.FileDialog(
            parent=gui.mainFrame,
            message="Open PGN File",
            defaultDir=wx.GetUserHome(),
            wildcard="Portable Game Notation *.pgn | *.pgn",
            style=wx.FD_OPEN,
        )
        gui.runScriptModalDialog(
            openFileDialog, functools.partial(self.list_games_in_pgn, openFileDialog)
        )

    def list_games_in_pgn(self, dialog, res):
        if res != wx.ID_OK:
            return
        filepath = dialog.GetPath().strip()
        if not filepath:
            return
        games = tuple(PGNGameInfo.game_info_from_pgn_filename(filepath))
        if not games:
            queueHandler.queueFunction(
                queueHandler.eventQueue, ui.message, "The file contains no games"
            )
        elif len(games) == 1:
            self.open_pgn_game(games[0])
        else:
            choiceDg = wx.SingleChoiceDialog(
                gui.mainFrame,
                _("The file contains the following games"),
                _("Select Game"),
                choices=[g.description for g in games],
            )
            gui.runScriptModalDialog(
                choiceDg,
                functools.partial(self.on_pgn_game_chosen, filepath, choiceDg, games),
            )

    def on_pgn_game_chosen(self, filepath, dialog, games, res):
        if res != wx.ID_OK:
            return
        selected_game_info = games[dialog.GetSelection()]
        self.open_pgn_game(selected_game_info)

    def open_pgn_game(self, game_Info):
        pgn_game = PGNGame.from_game_info(game_Info)
        chess_new_game_info = GameInfo(
            variant=None,
            time_control=NULL_TIME_CONTROL,
            pychess_board=None,
            prospective=None,
            vboard_kwargs=dict(game=pgn_game, use_visuals=True, visual_arrows=True),
        )
        self.global_plugin_object.initialize_and_show_chessboard_dialog(
            PGNPlayerChessboard,
            chess_new_game_info
        )


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active_board_dialogs = {}
        # The following is the GUI part
        if not globalVars.appArgs.secure:
            self.chessboard_menu = ChessboardMenu(self)

    def terminate(self):
        gui.mainFrame.sysTrayIcon.menu.DestroyItem(self.chessboard_menu.itemHandle)
        try:
            concurrency.terminate()
            for cdlg in self._active_board_dialogs:
                cdlg.Destroy()
        except:
            log.exception("Failed to terminate concurrency primitives")

    def initialize_and_show_chessboard_dialog(self, vboard_cls, game_info):
        chessboard_dialog = ChessboardDialog.from_game_info(vboard_cls, game_info)
        self._active_board_dialogs[chessboard_dialog.GetHandle()] = chessboard_dialog
        chessboard_dialog.Show()
        winUser.setForegroundWindow(chessboard_dialog.GetHandle())

    def event_gainFocus(self, obj, nextHandler):
        nextHandler()
        board_dialog = self._active_board_dialogs.get(obj.windowHandle)
        if (not board_dialog) or (not board_dialog.IsActive()):
            return
        if board_dialog.IsShown():
            queueHandler.queueFunction(
                queueHandler.eventQueue, board_dialog.set_focus_to_board
            )
