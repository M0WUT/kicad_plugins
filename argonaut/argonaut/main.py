# Standard imports

# Third party imports
import wx

# Local imports
from argonaut.misc.os import delete_folder, get_temp_dir_path
from argonaut.gui.main_frame import MainFrame
from argonaut.misc.git import validate_github_setup
from argonaut.config.config import DELETE_TEMP_FOLDER_ON_STARTUP


def main():
    if DELETE_TEMP_FOLDER_ON_STARTUP:
        delete_folder(get_temp_dir_path(create_folder=False))
    gh_user = validate_github_setup()

    app = wx.App(False)
    frame = MainFrame(gh_user)
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
