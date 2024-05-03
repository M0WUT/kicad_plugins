import platform
from pathlib import Path
import logging
from typing import Optional
import subprocess
from re import sub

from ui import show_error, show_info, show_warning, get_text_input
from github_helper import (
    check_if_github_cli_exists,
    check_if_project_exists,
    get_current_github_user,
)

from logging_handler import configure_logger


class KicadProjectCreator:
    def __init__(self, logging_level=logging.WARNING):

        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging_level)
        
        self.get_os_type()
        self.get_kicad_path()

   

    def get_os_type(self):
        self.os_type = platform.system()
        if self.os_type == "Windows":
            self.logger.debug("Detected Windows System")
        else:
            raise NotImplementedError

    def get_kicad_path(self):
        if self.os_type == "Windows":
            # Try local install
            home_directory = Path.home()
            test_directory = home_directory / "AppData" / "Local" / "Programs" / "Kicad"
            if test_directory.is_dir():
                kicad_folder = [x for x in test_directory.iterdir()][0] / "bin"
                self.kicad_path = kicad_folder / "kicad"
                self.kicad_cli_path = kicad_folder / "kicad-cli"
                self.logger.debug(f"Kicad found in {kicad_folder}")
            else:
                raise NotImplementedError




        

def main():
    x = KicadProjectCreator(logging.DEBUG)
    x.check_if_github_cli_exists()
    x.check_if_project_exists("M0WUT", "kicad_reeaser")


if __name__ == "__main__":
    main()
