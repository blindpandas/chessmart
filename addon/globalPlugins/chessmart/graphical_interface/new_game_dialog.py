# coding: utf-8

import random
import functools
import wx
import tones
import gui
from gui import guiHelper
from logHandler import log
from ..chessboard import GameInfo, ChessboardDialog
from ..helpers import import_bundled
from ..internet_chess import LichessAPIClient
from .components import EnumRadioBox, EnumChoice, AsyncSnakDialog
from ..game_elements import PlayMode, TimeControl, ChessVariant, PlayerColor
from ..time_control import ChessTimeControl
from ..internet_chess import (
    OperationTimeout,
    ChallengeRejected,
    InternetChessConnectionError,
    ChallengedUserIsOffline,
)


with import_bundled():
    import chess


class NewGameOptionsDialog(gui.SettingsDialog):
    title = "New Game Options"

    def __init__(self, *args, callback, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback
        self._uci_options = self._uci_time_limit = None

    def makeSettings(self, sizer):
        sizer.SetOrientation(wx.HORIZONTAL)
        mainSizerHelper = guiHelper.BoxSizerHelper(self, sizer=sizer)
        primaryOptionsSizerHelper = guiHelper.BoxSizerHelper(
            self, orientation=wx.VERTICAL
        )
        secondaryOptionsSizerHelper = guiHelper.BoxSizerHelper(
            self, orientation=wx.VERTICAL
        )
        intro_label = wx.StaticText(
            self,
            -1,
            _("Choose the play mode, starting position, and time control."),
            style=wx.ST_ELLIPSIZE_MIDDLE,
        )
        intro_label.Wrap(self.GetSize().Width)
        primaryOptionsSizerHelper.addItem(intro_label)
        # Play mode
        self.playModeRadioBox = EnumRadioBox(
            self,
            wx.ID_ANY,
            label=_("Play Mode"),
            choice_enum=PlayMode,
            majorDimension=0,
            style=wx.RA_SPECIFY_ROWS,
        )
        primaryOptionsSizerHelper.addItem(self.playModeRadioBox)
        # Starting position
        chessVariantLabel = wx.StaticText(self, -1, _("Variant"))
        self.chessVariantChoice = EnumChoice(
            self,
            wx.ID_ANY,
            choice_enum=ChessVariant,
        )
        primaryOptionsSizerHelper.addItem(chessVariantLabel)
        primaryOptionsSizerHelper.addItem(self.chessVariantChoice)
        # Time Control
        timeControlLabel = wx.StaticText(self, -1, _("Time Control"))
        self.timeControlRadioBox = EnumChoice(
            self,
            wx.ID_ANY,
            choice_enum=TimeControl,
        )
        guiHelper.associateElements(timeControlLabel, self.timeControlRadioBox)
        primaryOptionsSizerHelper.addItem(timeControlLabel)
        primaryOptionsSizerHelper.addItem(self.timeControlRadioBox)
        # Player color
        self.playerColorRadioBox = EnumRadioBox(
            self,
            wx.ID_ANY,
            label=_("Play As"),
            choice_enum=PlayerColor,
            majorDimension=1,
            style=wx.RA_SPECIFY_ROWS,
        )
        secondaryOptionsSizerHelper.addItem(self.playerColorRadioBox)
        # Custom starting FEN
        customFENLabel = wx.StaticText(
            self, -1, _("Starting FEN")
        )
        self.customStartingFEN  = wx.TextCtrl(self, -1)
        guiHelper.associateElements(customFENLabel, self.customStartingFEN)
        secondaryOptionsSizerHelper.addItem(customFENLabel)
        secondaryOptionsSizerHelper.addItem(self.customStartingFEN)
        # Custom Time Control
        customTimeControlLable = wx.StaticText(self, -1, _("Custom Time Control"))
        self.customTimeControlTextCtrl = wx.TextCtrl(self, -1)
        guiHelper.associateElements(
            customTimeControlLable, self.customTimeControlTextCtrl
        )
        secondaryOptionsSizerHelper.addItem(customTimeControlLable)
        secondaryOptionsSizerHelper.addItem(self.customTimeControlTextCtrl)
        # Engine options
        self.engineOptionsButton = wx.Button(self, -1, _("Engine &Options..."))
        secondaryOptionsSizerHelper.addItem(self.engineOptionsButton)
        # Rated play
        self.playRatedGameCheckbox = wx.CheckBox(self, -1, _("Play &Rated Game"))
        secondaryOptionsSizerHelper.addItem(self.playRatedGameCheckbox)
        # Use visuals
        self.useVisualsCheckbox = wx.CheckBox(
            self, -1, label=_("Visually highlight board interactions")
        )
        secondaryOptionsSizerHelper.addItem(self.useVisualsCheckbox)
        # Online play buttons
        onlinePlayButtonsSizerHelper = guiHelper.BoxSizerHelper(
            self, orientation=wx.HORIZONTAL
        )
        self.seekGameButton = wx.Button(self, -1, _("&Seek Game"))
        self.createChallengeButton = wx.Button(self, -1, _("Create &challenge"))
        onlinePlayButtonsSizerHelper.addItem(self.seekGameButton)
        onlinePlayButtonsSizerHelper.addItem(self.createChallengeButton)
        secondaryOptionsSizerHelper.addItem(onlinePlayButtonsSizerHelper)
        # Add sizers to the main sizer
        mainSizerHelper.addItem(primaryOptionsSizerHelper)
        mainSizerHelper.addItem(secondaryOptionsSizerHelper)
        # Bind events
        self.Bind(wx.EVT_RADIOBOX, self.onPlayModeRadio, self.playModeRadioBox)
        self.Bind(wx.EVT_CHOICE, self.onTimeControlRadio, self.timeControlRadioBox)
        self.Bind(wx.EVT_BUTTON, self.onEngineOptions, self.engineOptionsButton)
        self.Bind(wx.EVT_BUTTON, self.onSeekGame, self.seekGameButton)
        self.Bind(wx.EVT_BUTTON, self.onCreateChallenge, self.createChallengeButton)

    def postInit(self):
        self.playModeRadioBox.SetFocus()
        self.customTimeControlTextCtrl.Enable(
            self.timeControlRadioBox.SelectedValue is TimeControl.CUSTOM
        )
        initial_play_mode = self.playModeRadioBox.GetSelectedValue()
        self.engineOptionsButton.Enable(
            initial_play_mode is PlayMode.HUMAN_VERSUS_COMPUTER
        )
        self.seekGameButton.Enable(initial_play_mode is PlayMode.ONLINE_LICHESS_ORG)
        self.createChallengeButton.Enable(
            initial_play_mode is PlayMode.ONLINE_LICHESS_ORG
        )
        self.playRatedGameCheckbox.Enable(
            initial_play_mode is PlayMode.ONLINE_LICHESS_ORG
        )

    def get_game_info(self):
        try:
            time_control = self._get_time_control()
        except ValueError:
            gui.messageBox(
                _(
                    "Please enter a valid time control string.\nExample: 10+5 for a 10 minutes base time with 5 seconds increment after each move."
                ),
                _("Invalid Time Control String"),
                style=wx.ICON_ERROR,
            )
            return
        try:
            pychess_board = self._get_pychess_board()
        except ValueError:
            gui.messageBox(
                _(
                    "Please enter a valid starting FEN.\nExample:\n{fen}\nfor a standard starting FEN."
                ).format(fen=chess.STARTING_FEN),
                _("Invalid FEN String"),
                style=wx.ICON_ERROR,
            )
            return
        game_info = GameInfo(
            pychess_board=pychess_board,
            variant=self.chessVariantChoice.GetSelectedValue(),
            time_control=time_control,
            prospective=self.playerColorRadioBox.GetSelectedValue().get_color(),
            custom_starting_fen=self.customStartingFEN.GetValue().strip()
        )
        game_info.vboard_kwargs["use_visuals"] = self.useVisualsCheckbox.IsChecked()
        if self.playModeRadioBox.GetSelectedValue() == PlayMode.HUMAN_VERSUS_COMPUTER:
            game_info.vboard_kwargs.update(dict(
                uci_options=self._uci_options,
                uci_time_limit=self._uci_time_limit,
            ))
        return game_info

    def onOk(self, event):
        if self.playModeRadioBox.GetSelectedValue() == PlayMode.ONLINE_LICHESS_ORG:
            return
        game_info = self.get_game_info()
        vboard_cls = self.playModeRadioBox.GetSelectedValue().get_board_class()
        self.callback(vboard_cls, game_info)
        super().onOk(event)

    def onPlayModeRadio(self, event):
        selectedValue = event.GetEventObject().GetSelectedValue()
        self.playerColorRadioBox.Enable(
            selectedValue is not PlayMode.HUMAN_VERSUS_HUMAN
        )
        self.engineOptionsButton.Enable(selectedValue is PlayMode.HUMAN_VERSUS_COMPUTER)
        self.seekGameButton.Enable(selectedValue is PlayMode.ONLINE_LICHESS_ORG)
        self.createChallengeButton.Enable(selectedValue is PlayMode.ONLINE_LICHESS_ORG)
        self.playRatedGameCheckbox.Enable(selectedValue is PlayMode.ONLINE_LICHESS_ORG)
        self.GetDefaultItem().Enable(selectedValue is not PlayMode.ONLINE_LICHESS_ORG)

    def onTimeControlRadio(self, event):
        if event.GetEventObject().GetSelectedValue() is not TimeControl.CUSTOM:
            self.customTimeControlTextCtrl.SetValue("")
            self.customTimeControlTextCtrl.Enable(False)
        else:
            self.customTimeControlTextCtrl.Enable()

    def onEngineOptions(self, event):
        saved_options = {}
        if self._uci_options and "UCI_Elo" in self._uci_options:
            saved_options["engine_elo_rating"] = self._uci_options["UCI_Elo"]
        if self._uci_time_limit is not None:
            saved_options["engine_limit"] = self._uci_time_limit
        dialog = UCIEngineOptionsDialog(self, saved_options=saved_options)
        dialog.Show()

    def onSeekGame(self, event):
        game_info = self.get_game_info()
        client = LichessAPIClient(game_info)
        is_rated = self.playRatedGameCheckbox.IsChecked()
        chessboard_cls = self.playModeRadioBox.GetSelectedValue().get_board_class()
        super().onOk(event)
        task = client.seek_game(
            rated=is_rated,
            timeout=30,
        )
        dg = AsyncSnakDialog(
            task=task,
            parent=None,
            message=f"Seeking game...",
            done_callback=functools.partial(self._on_lichess_api_callback, chessboard_cls, game_info),
            dismiss_callback=lambda: 1,
        )

    def onCreateChallenge(self, event):
        challenge_whom = wx.GetTextFromUser(
            _("Enter the user name of the user you want to challenge:"),
            _("Challenge whom?"),
            parent=self,
        ).strip()
        if not challenge_whom:
            return
        game_info = self.get_game_info()
        client = LichessAPIClient(game_info)
        is_rated = self.playRatedGameCheckbox.IsChecked()
        chessboard_cls = self.playModeRadioBox.GetSelectedValue().get_board_class()
        super().onOk(event)
        task = client.create_challenge(
            opponent_username=challenge_whom,
            rated=is_rated,
            timeout=30,
        )
        dg = AsyncSnakDialog(
            task=task,
            parent=None,
            message=f"Creating Challenge with {challenge_whom}...",
            done_callback=functools.partial(self._on_lichess_api_callback, chessboard_cls, game_info),
            dismiss_callback=lambda: 1,
        )

    def _on_lichess_api_callback(self, chessboard_cls, game_info, future):
        try:
            board_client = future.result()
            if not board_client:
                raise ValueError("Invalid chessboard client")
            game_info.vboard_kwargs["client"] = board_client
            wx.CallAfter(
                self.callback,
                chessboard_cls,
                game_info
            )
        except InternetChessConnectionError:
            wx.CallAfter(
                gui.messageBox,
                _("Failed to connect to lichess.org. Please try again later."),
                _("Connection Error"),
                style=wx.ICON_ERROR,
            )
        except OperationTimeout:
            wx.CallAfter(
                gui.messageBox,
                _("Operation timeout. Please try again."),
                _("Error"),
                style=wx.ICON_ERROR,
            )
        except ChallengeRejected:
            wx.CallAfter(
                gui.messageBox,
                _("Your challenge has been rejected. Please try again."),
                _("Rejected"),
                style=wx.ICON_ERROR,
            )
        except ChallengedUserIsOffline as e_offline:
            wx.CallAfter(
                gui.messageBox,
                _(
                    "User {user} is currently offline. Please try again when the user is online."
                ).format(user=e_offline.username),
                _("User Offline"),
                style=wx.ICON_INFORMATION,
            )

    def set_engine_options(self, options):
        self._uci_options, self._uci_time_limit = options

    def _get_pychess_board(self):
        selected_variant = self.chessVariantChoice.GetSelectedValue()
        board_cls = selected_variant.get_board()
        custom_starting_FEN = self.customStartingFEN.GetValue().strip()
        if custom_starting_FEN:
            return  board_cls(custom_starting_FEN)
        elif selected_variant is ChessVariant.CHESS960:
            return chess.Board.from_chess960_pos(random.randint(0, 959))
        else:
            return board_cls() 

    def _get_time_control(self):
        time_control = self.timeControlRadioBox.GetSelectedValue().get_time_control()
        if time_control is None:
            time_control = ChessTimeControl.from_time_control_notation(
                self.customTimeControlTextCtrl.GetValue()
            )
        return time_control


class UCIEngineOptionsDialog(gui.SettingsDialog):
    title = _("Engine Options")

    def __init__(self, *args, saved_options=None, **kwargs):
        self.saved_options = saved_options or {}
        super().__init__(*args, **kwargs)

    def makeSettings(self, sizer):
        mainSizerHelper = guiHelper.BoxSizerHelper(self, sizer=sizer)
        primaryOptionsSizerHelper = guiHelper.BoxSizerHelper(
            self, orientation=wx.VERTICAL
        )
        engineSkillLevelLabel = wx.StaticText(
            self, -1, _("Engine Strength (ELO Rating)")
        )
        self.engineSkillLevel = wx.SpinCtrl(self, -1, min=1350, max=2850)
        guiHelper.associateElements(engineSkillLevelLabel, self.engineSkillLevel)
        primaryOptionsSizerHelper.addItem(engineSkillLevelLabel)
        primaryOptionsSizerHelper.addItem(self.engineSkillLevel)
        # Thinking time
        thinkingLimitLabel = wx.StaticText(
            self, -1, _("Engine Thinking Time (in seconds)")
        )
        self.thinkingLimitSpin = wx.SpinCtrl(self, -1, min=1, max=300)
        guiHelper.associateElements(thinkingLimitLabel, self.thinkingLimitSpin)
        primaryOptionsSizerHelper.addItem(thinkingLimitLabel)
        primaryOptionsSizerHelper.addItem(self.thinkingLimitSpin)
        mainSizerHelper.addItem(primaryOptionsSizerHelper)

    def postInit(self):
        self.engineSkillLevel.SetValue(
            self.saved_options.get("engine_elo_rating", 1350)
        )
        self.thinkingLimitSpin.SetValue(self.saved_options.get("engine_limit", 2))
        self.engineSkillLevel.SetFocus()

    def onOk(self, event):
        self.Parent.set_engine_options(self.get_options())
        super().onOk(event)

    def get_options(self):
        uci_options = dict(
            UCI_LimitStrength=True,
            UCI_Elo=self.engineSkillLevel.GetValue(),
        )
        return (
            uci_options,
            self.thinkingLimitSpin.GetValue(),
        )
