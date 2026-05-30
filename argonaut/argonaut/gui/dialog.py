# Standard imports
from pathlib import Path
import sys
from typing import Optional

# Third party imports
import wx

# Local imports


class ChoiceDialog(wx.Dialog):
    def __init__(
        self, parent: Optional[wx.Window], title: str, options: list[str]
    ) -> None:
        super().__init__(parent, title=title, size=wx.Size(300, 400))

        self.selected_option: Optional[str] = None

        # Main vertical layout
        vbox = wx.BoxSizer(wx.VERTICAL)

        # List of options
        self.listbox = wx.ListBox(
            self,
            choices=list(options),
            style=wx.LB_SINGLE,
        )
        vbox.Add(self.listbox, 1, wx.ALL | wx.EXPAND, 10)

        # Double-click handler
        self.listbox.Bind(wx.EVT_LISTBOX_DCLICK, self.on_double_click)

        # Cancel button
        cancel_btn = wx.Button(self, label="Cancel")
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        vbox.Add(cancel_btn, 0, wx.ALL | wx.ALIGN_CENTER, 10)

        self.SetSizer(vbox)

    def on_double_click(self, event: wx.CommandEvent) -> None:
        selection = self.listbox.GetStringSelection()
        if selection:
            self.selected_option = selection

        self.EndModal(wx.ID_OK)

    def on_cancel(self, event: wx.CommandEvent) -> None:
        self.selected_option = None
        self.EndModal(wx.ID_CANCEL)


def get_user_choice(
    parent: Optional[wx.Window],
    options: list[str],
    title: str = "Select an option",
) -> Optional[str]:
    """
    Display a modal dialog containing a list of options.

    Double-clicking an option returns the selected string.
    Pressing Cancel returns None.
    """
    dlg = ChoiceDialog(parent, title, options)

    try:
        dlg.ShowModal()
        return dlg.selected_option
    finally:
        dlg.Destroy()


def _show_message(message: str, title: str, style: int) -> int:
    dlg = wx.MessageDialog(
        parent=None,
        message=message,
        caption=title,
        style=style,
    )
    ret = dlg.ShowModal()
    dlg.Destroy()

    if ret not in [wx.ID_OK, wx.ID_YES, wx.ID_NO]:
        sys.exit(0)
    return ret


def show_info(message: str, title: str) -> int:
    return _show_message(message, title, style=wx.OK | wx.CANCEL | wx.ICON_INFORMATION)


def show_warning(message: str, title: str) -> int:
    return _show_message(message, title, style=wx.OK | wx.CANCEL | wx.ICON_WARNING)


def show_error(message: str, title: str, exit_on_error: bool = True) -> int:
    ret = _show_message(message, title, style=wx.OK | wx.ICON_ERROR)
    if exit_on_error:
        sys.exit(0)
    else:
        return ret


def abort():
    show_error("User aborted", "Aborted")


def ask_question(message: str, title: str) -> bool:
    return _show_message(message, title, style=wx.YES | wx.NO) == wx.ID_YES


def get_text_input(message: str = "", title: str = "Text Input") -> str:
    dlg = wx.TextEntryDialog(parent=None, message=message, caption=title)
    ret = dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    if ret != wx.ID_OK:
        sys.exit(1)
    return result


def get_folder_input(message: str = "") -> Path:
    dlg = wx.DirDialog(
        parent=None,
        message=message,
        name="",
        style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
    )
    ret = dlg.ShowModal()
    result = dlg.GetPath()
    dlg.Destroy()

    if ret != wx.ID_OK:
        sys.exit(1)

    return Path(result)
