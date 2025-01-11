import logging
import re

from ..utils.github_helper import (
    check_if_github_cli_exists,
    check_if_project_exists,
    get_current_github_user,
    git_checkout,
    git_push,
)
from ..utils.platform import delete_folder, get_temp_path
from ..utils.ui import (
    get_folder_input,
    get_text_input,
    show_error,
    show_info,
    show_warning,
)
from .config import BOARD_TRACKER_PROJECT_USER, BOARD_TRACKER_REPO
from .logging_handler import configure_logger


class ProjectCreator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)

    def ask_project_name(self):
        self.project_name = None
        self.repo_name = None

        while self.project_name is None:
            requested_project_name = get_text_input(
                message="Please enter requested repo name",
                title="Enter repo name",
            )

            requested_repo_name = re.sub(
                " ", "-", requested_project_name.lower()
            )
            if (
                check_if_project_exists(self.gh_user, requested_repo_name)
                is False
            ):
                # New project name
                self.project_name = requested_project_name
                self.repo_name = requested_repo_name
                self.logger.info(
                    f'Creating project "{self.project_name}" at'
                    f"github.com/{self.gh_user}/"
                    f"{self.repo_name}"
                )
            else:
                show_warning(
                    f"Repo {self.gh_user}/{requested_repo_name}'"
                    " already exists",
                    "Repo already exists",
                )

    def get_project_info(self):
        # Check if Github CLI is present
        if check_if_github_cli_exists() is False:
            show_error(
                "Github CLI not found. Please ensure it is"
                "installed and authenticated",
                "Github CLI not found",
            )

        # Query for Github user
        self.gh_user = get_current_github_user()
        self.logger.info(f"Github user detected as {self.gh_user}")

        # Get an new project name
        self.ask_project_name()

        # Create blank repo
        show_info(
            f"This will create a default Kicad project in the {self.gh_user}/"
            f"{self.repo_name} repository. Press OK to continue...",
            title="Here we go!",
        )
        # create_blank_github_repo(repo_name)
        # self.logger.info(f"{gh_user}/{repo_name} created")

        # Select parent folder for checkout
        self.repo_parent_folder = get_folder_input(
            "Please select parent directory for checkout",
            "Select parent folder",
        )

    def reserve_board_number(self, board_name: str) -> int:
        try:
            # Checkout tracker repo
            boards_tracker_path = get_temp_path() / "M0WUT"
            boards_tracker_path.mkdir(parents=True)
            git_checkout(
                BOARD_TRACKER_PROJECT_USER,
                BOARD_TRACKER_REPO,
                boards_tracker_path,
            )

            # Extract previous board number and add new board to the file
            with open(boards_tracker_path / "boards.csv", "r") as boards_file:

                existing_boards = boards_file.readlines()
                if existing_boards:
                    board_number = 1 + int(existing_boards[-1].split(",")[0])
                else:
                    board_number = 1

                self.logger.info(f"Creating board number {board_number}")

            with open(boards_tracker_path / "boards.csv", "a") as boards_file:
                boards_file.write(f'{board_number},"{board_name}"\n')

            # Check in the changes
            git_push(boards_tracker_path, f"Added board number {board_number}")

            return board_number

        finally:
            delete_folder(boards_tracker_path)

    def run(self):
        self.get_project_info()
        self.project_number = self.reserve_board_number(self.project_name)


def run():
    x = ProjectCreator()
    x.run()


if __name__ == "__main__":
    run()
