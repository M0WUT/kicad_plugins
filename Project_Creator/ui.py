import sys
from pathlib import Path

import wx  # type: ignore


def _show_message(message: str, title: str, style: int) -> None:
    dlg = wx.MessageDialog(
        parent=None,
        message=message,
        caption=title,
        style=style,
    )
    ret = dlg.ShowModal()
    dlg.Destroy()

    if ret != wx.ID_OK:
        sys.exit(0)


def show_info(message: str, title: str):
    _show_message(message, title, style=wx.OK | wx.ICON_INFORMATION)


def show_warning(message: str, title: str):
    _show_message(message, title, style=wx.OK | wx.ICON_WARNING)


def show_error(message: str, title: str, exit_on_error: bool = True):
    _show_message(message, title, style=wx.OK | wx.ICON_ERROR)
    if exit_on_error:
        sys.exit(0)


def get_text_input(message: str = "", title: str = "Text Input") -> str:
    dlg = wx.TextEntryDialog(parent=None, message=message, caption=title)
    ret = dlg.ShowModal()
    result = dlg.GetValue()
    dlg.Destroy()
    if ret != wx.ID_OK:
        sys.exit(1)
    return result


def get_folder_input(message: str = "", title: str = "") -> Path:
    dlg = wx.DirDialog(
        parent=None,
        message=message,
        name=title,
        style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
    )
    ret = dlg.ShowModal()
    result = dlg.GetPath()
    dlg.Destroy()

    if ret != wx.ID_OK:
        sys.exit(1)

    return Path(result)


def main():
    _ = wx.App()
    get_folder_input()


if __name__ == "__main__":
    main()
