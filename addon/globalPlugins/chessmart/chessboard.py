# coding: utf-8

import os
import math
import subprocess
import wx
import wx.adv
import tones
import queueHandler
import eventHandler
import gui
from io import BytesIO
from .game_elements import GameInfo
from .helpers import import_bundled, BIN_DIRECTORY, GameSound
from .signals import (
    chessboard_opened_signal,
    chessboard_closed_signal,
    move_completed_signal,
)
from .time_control import ChessTimeControl
from .concurrency import call_threaded


with import_bundled():
    from wx_svg import SVGimage
    import chess
    import chess.svg


TIME_CHECK_INTERVAL = 1000
RSVG_CONVERT_EXECUTABLE = os.path.join(
    BIN_DIRECTORY, "rsvg_convert", "rsvg_convert.exe"
)
BOARD_COLOR_MAP = {
    "square light": "#ff7187fe",
    "square dark": "#cd3721ff",
    "square light lastmove": "#c88771ff",
    "square dark lastmove": "#e63721ff",
    "margin": "",
    "coord": "",
}


class ChessboardDialog(wx.Frame):
    """GUI of the chessboard."""

    def __init__(self, chessboard_class, **vboard_kwargs):
        super().__init__()
        super().Create(title="Chess Board", parent=gui.mainFrame, style=wx.NO_BORDER)
        self.chessboard_class = chessboard_class
        self.vboard_kwargs = vboard_kwargs
        self.SetName("Chessboard")
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        size = wx.Size(900, 900)
        self.width, self.height = size
        self.SetMinSize(size)
        self.SetSize(size)
        self.CenterOnScreen()
        self.bitmap_buffer = wx.EmptyBitmap(*size)
        self.Bind(wx.EVT_PAINT, self.onPaint, self)
        self.Bind(wx.EVT_CLOSE, self.onClose, self)
        # Setup the board
        self.chessboard = None
        # Time related stuff
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onChessTimer, id=self.timer.GetId())
        self.notification_records = {
            color: {i: False for i in range(1, 8)} for color in chess.COLORS
        }

    @classmethod
    def from_game_info(cls, vboard_cls, game_info: GameInfo):
        vboard_kwargs = dict(
            pychess_board=game_info.pychess_board,
            variant=game_info.variant,
            prospective=game_info.prospective,
            time_control=game_info.time_control,
        )
        vboard_kwargs.update(game_info.vboard_kwargs)
        return cls(chessboard_class=vboard_cls, **vboard_kwargs)

    def set_focus_to_board(self):
        if self.chessboard is None:
            self.chessboard = self.chessboard_class(dialog=self, **self.vboard_kwargs)
            queueHandler.queueFunction(
                queueHandler.eventQueue, GameSound.start_game.play
            )
            chessboard_opened_signal.send(self.chessboard)
            self.timer.Start(TIME_CHECK_INTERVAL, wx.TIMER_CONTINUOUS)
            self.set_board_image()
        eventHandler.executeEvent("gainFocus", self.chessboard)

    def get_board_svg(self, board=None, **chess_svg_kwargs):
        if "flipped" not in chess_svg_kwargs:
            chess_svg_kwargs["flipped"] = self.chessboard.is_board_visually_flipped
        return chess.svg.board(
            board or self.chessboard.board,
            colors=BOARD_COLOR_MAP,
            **chess_svg_kwargs
        ).encode("utf-8")

    def onPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush("white"))
        dc.Clear()
        if self.chessboard is None:
            ctx = wx.GraphicsContext.Create(dc)
            board_svg = self.get_board_svg(
                chess.Board(), size=self.width, flipped=False
            )
            svg_image = SVGimage.CreateFromBytes(board_svg)
            svg_image.RenderToGC(ctx, 1)
        else:
            dc.DrawBitmap(self.bitmap_buffer, 0, 0)

    def onClose(self, event):
        event.Skip()
        self.timer.Stop()
        chessboard_closed_signal.send(self.chessboard)

    def onChessTimer(self, event):
        time_control = self.chessboard.time_control
        if self.chessboard.is_game_over:
            time_control.stop()
            self.timer.Stop()
            return
        time_forfeit = time_control.is_time_forfeit()
        if any(time_forfeit.values()):
            losing_color = chess.WHITE if time_forfeit[chess.WHITE] else chess.BLACK
            self.chessboard.game_time_forfeit(losing_color)
            return
        current_player = self.chessboard.board.turn
        remaining = time_control.percentage_remaining(current_player) / 10
        if self.notification_records[current_player].get(remaining, True):
            return
        self.notification_records[current_player][remaining] = True
        if remaining >= 3:
            sound = GameSound.time_pass
        else:
            sound = GameSound.time_critical
        wx.adv.Sound(sound.filename).Play(wx.adv.SOUND_ASYNC)

    def set_board_image(self, **chess_svg_kwargs):
        board_svg_bytes = self.get_board_svg(**chess_svg_kwargs)
        self._get_png_from_svg(board_svg_bytes).add_done_callback(self.set_background_png)

    @call_threaded
    def _get_png_from_svg(self, board_svg_bytes):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.run(
            [
                RSVG_CONVERT_EXECUTABLE,
                "-f",
                "png",
                "-w",
                str(self.width),
                "-h",
                str(self.height),
            ],
            input=board_svg_bytes,
            capture_output=True,
            startupinfo=startupinfo,
        )

    def set_background_png(self, future):
        sp_result = future.result()
        if sp_result.returncode != 0:
            log.exception("Failed to convert svg to png.\n{sp_result.stderr}")
            return
        board_image = wx.Image(BytesIO(sp_result.stdout))
        wx.CallAfter(self._set_bitmap_data, board_image.GetData())

    def _set_bitmap_data(self, data):
        self.bitmap_buffer.CopyFromBuffer(data)
        self.Refresh(eraseBackground=False)
        self.Update()
