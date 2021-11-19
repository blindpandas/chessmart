# coding: utf-8

import typing as t
import threading
import contextlib
import wx
import gui
from ..helpers import import_bundled


with import_bundled():
    import wx_lib_sized_controls as sc


LongRunningTask = t.Callable[[t.Any], t.Any]
DoneCallback = t.Callable[["Future"], None]


class SimpleDialog(sc.SizedDialog):
    """Basic dialog for simple  GUI forms."""

    def __init__(self, parent, title, style=wx.DEFAULT_DIALOG_STYLE, **kwargs):
        super().__init__(parent, title=title, style=style, **kwargs)
        self.parent = parent

        panel = self.GetContentsPane()
        self.addControls(panel)
        buttonsSizer = self.getButtons(panel)
        if buttonsSizer is not None:
            self.SetButtonSizer(buttonsSizer)

        self.Layout()
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Center(wx.BOTH)

    def SetButtonSizer(self, sizer):
        bottomSizer = wx.BoxSizer(wx.VERTICAL)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        bottomSizer.Add(line, 0, wx.TOP | wx.EXPAND, 15)
        bottomSizer.Add(sizer, 0, wx.EXPAND | wx.ALL, 10)
        super().SetButtonSizer(bottomSizer)

    def addControls(self, parent):
        raise NotImplementedError

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of the OK button in a dialog
        okBtn = wx.Button(self, wx.ID_OK, _("OK"))
        okBtn.SetDefault()
        # Translators: the label of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        for btn in (okBtn, cancelBtn):
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        return btnsizer


class SnakDialog(SimpleDialog):
    """A Toast style notification  dialog for showing a simple message without a title."""

    def __init__(self, message, *args, dismiss_callback=None, **kwargs):
        self.message = message
        self.dismiss_callback = dismiss_callback
        kwargs.setdefault("parent", gui.mainFrame)
        super().__init__(*args, title="", style=0, **kwargs)
        self.CenterOnParent()

    def addControls(self, parent):
        ai = wx.ActivityIndicator(parent)
        ai.SetSizerProp("halign", "center")
        self.staticMessage = wx.StaticText(parent, -1, self.message)
        self.staticMessage.SetCanFocus(True)
        self.staticMessage.SetFocusFromKbd()
        self.Bind(wx.EVT_CLOSE, self.onClose, self)
        self.staticMessage.Bind(wx.EVT_KEY_UP, self.onKeyUp, self.staticMessage)
        ai.Start()

    @contextlib.contextmanager
    def ShowBriefly(self):
        try:
            wx.CallAfter(self.ShowModal)
            yield
        finally:
            wx.CallAfter(self.Close)
            wx.CallAfter(self.Destroy)

    def onClose(self, event):
        if event.CanVeto():
            if self.dismiss_callback is not None:
                should_close = self.dismiss_callback()
                if should_close:
                    self.Hide()
                    return
            event.Veto()
        else:
            self.Destroy()

    def onKeyUp(self, event):
        event.Skip()
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()

    def getButtons(self, parent):
        return


class AsyncSnakDialog:
    """A helper to make the use of SnakDialogs Ergonomic."""

    def __init__(
        self,
        task: LongRunningTask,
        done_callback: DoneCallback,
        *sdg_args,
        **sdg_kwargs,
    ):
        self.snak_dg = SnakDialog(*sdg_args, **sdg_kwargs)
        self.done_callback = done_callback
        self.future = task.add_done_callback(self.on_future_completed)
        self.snak_dg.Show()

    def on_future_completed(self, completed_future):
        self.Dismiss()
        wx.CallAfter(self.done_callback, completed_future)

    def Dismiss(self):
        if self.snak_dg:
            wx.CallAfter(self.snak_dg.Hide)
            wx.CallAfter(self.snak_dg.Destroy)


class EnumItemContainerMixin:
    """An item container that accepts a DisplayStringIntEnum as its choices argument."""

    items_arg = None

    def __init__(self, *args, choice_enum, **kwargs):
        kwargs[self.items_arg] = [m.displayString for m in choice_enum]
        super().__init__(*args, **kwargs)
        self.choice_enum = choice_enum
        self.choice_members = tuple(choice_enum)
        if self.choice_members:
            self.SetSelection(0)

    def GetSelectedValue(self):
        return self.choice_members[self.GetSelection()]

    @property
    def SelectedValue(self):
        return self.GetSelectedValue()

    def SetSelectionByValue(self, value):
        if not isinstance(value, self.choice_enum):
            raise TypeError(f"{value} is not a {self.choice_enum}")
        self.SetSelection(self.choice_members.index(value))


class EnumRadioBox(EnumItemContainerMixin, wx.RadioBox):
    """A RadioBox that accepts enum as choices."""

    items_arg = "choices"


class EnumChoice(EnumItemContainerMixin, wx.Choice):
    items_arg = "choices"
