import logging
from pathlib import Path
import re
import csv
from typing import Optional

import git

from .git_functions import get_git_info
from .gh_functions import (
    create_blank_github_repo,
    check_github_project_exists,
    git_clone,
    validate_github_setup,
)
from .os_functions import delete_folder, get_temp_path
from .ui import (
    get_folder_input,
    get_text_input,
    show_error,
    show_info,
)
from .config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    TEMP_FOLDER_NAME,
)
from .logging_handler import configure_logger


class KicadProjectHandler:
    """
    Class for handling creation of a single Kicad Project within a larger Project
    """

    def __init__(self, gh_user: str):
        self.gh_user = gh_user
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def create_new_project(self):
        self.select_local_folder()

    def select_local_folder(self):
        local_folder_path = get_folder_input(
            "Select parent folder for new Kicad project"
        )
        self.logger.info(f"Selected local path for project: {local_folder_path}")

        # Three options here:
        #   In the "hardware" subfolder of a project top-level repo
        #   In a project top-level repo
        #   Not in a child of a project repo (may or may not be in a Git repo)

        self.logger.info(get_git_info(local_folder_path))

        # if local_folder_path.parent.stem == "hardware":
        #     pass
