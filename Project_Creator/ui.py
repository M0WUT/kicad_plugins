import sys
from pathlib import Path

import wx  # type: ignore


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


def main():
    _ = wx.App()
    print(show_info("Test", "title"))
    print(ask_question("Test", "title"))


if __name__ == "__main__":
    main()
