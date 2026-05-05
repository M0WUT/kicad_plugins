import logging
from pathlib import Path
import re
import csv
from typing import Optional

from git import InvalidGitRepositoryError


from project_creator.src.git_functions import (
    ensure_git_repo_up_to_date,
    get_git_info,
    git_commit_and_push,
)
from project_creator.src.gh_functions import (
    create_blank_github_repo,
    check_github_project_exists,
    git_clone,
    validate_github_setup,
)
from project_creator.src.os_functions import delete_folder, get_temp_dir_path
from project_creator.ui import (
    ask_question,
    get_folder_input,
    get_text_input,
    show_error,
    show_info,
    show_warning,
)
from project_creator.src.config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    TEMP_FOLDER_NAME,
)
from project_creator.src.logging_handler import configure_logger


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

    def select_local_hardware_folder(self) -> Path:
        local_folder_path = get_folder_input(
            "Select parent folder for new Kicad project"
        )
        self.logger.info(f"Selected local path for project: {local_folder_path}")

        # Three options here:
        #   1) In the "hardware" subfolder of a project top-level repo
        #   2) In a project top-level repo
        #   3) Not in a child of a project repo (may or may not be in a Git repo)

        try:
            ensure_git_repo_up_to_date(local_folder_path)
            git_info = get_git_info(local_folder_path)
            self.logger.info(git_info)

            # Option 2
            possible_hardware_folder_path = local_folder_path / "hardware"
            if (
                possible_hardware_folder_path.exists()
                and possible_hardware_folder_path.is_dir()
            ):
                # Hardware folder is already created
                self.logger.info(
                    f'Found hardware folder at "{possible_hardware_folder_path}"'
                )
                return possible_hardware_folder_path
            else:
                # Project repository does not yet have hardware folder
                if ask_question(
                    f'OK to create hardware folder for repo "{git_info.upstream}"?',
                    "Create hardware folder?",
                ):
                    possible_hardware_folder_path.mkdir(mode=660)
                    return possible_hardware_folder_path
                else:
                    show_error("User Aborted", "User aborted")

        except InvalidGitRepositoryError:
            if local_folder_path.stem == "hardware":
                try:
                    # Option 1
                    ensure_git_repo_up_to_date(local_folder_path.parent)
                    git_info = get_git_info(local_folder_path.parent)
                    self.logger.info(git_info)
                    # Option 1 - already there
                    self.logger.info(f'Using hardware folder at "{local_folder_path}"')
                    return local_folder_path
                except InvalidGitRepositoryError:
                    pass

            # Option 3
            self.logger.info(
                "Selected folder is not in a Git repo or its subdirectories"
            )

            # Could possibly do something nicer e.g. allow user to select which repo
            # they want to base this on but not bothering for now
            show_warning(
                "Selected folder is not a Git repository",
                "Not a Git Repo",
            )
            raise NotImplementedError

    def get_board_tracker_info(self, board_tracker_path: Path) -> list[list[str]]:
        try:
            with open(board_tracker_path, "r") as boards_file:
                project_tracker_reader = csv.reader(
                    boards_file, quotechar='"', delimiter=","
                )
                existing_boards = [x for x in project_tracker_reader]
            self.logger.info(f"Loaded info on {len(existing_boards)} boards")
            return existing_boards
        except FileNotFoundError:
            self.logger.warning("Board tracking csv not found. Creating blank file")
            return []

    def generate_next_board_number(self, board_tracker_path: Path) -> int:
        existing_boards = self.get_board_tracker_info(board_tracker_path)
        if existing_boards:
            highest_board_number = int(existing_boards[-1][0])
            if set([int(x[0]) for x in existing_boards]) != set(
                [x for x in range(1, 1 + highest_board_number)]
            ):
                show_error(
                    f"Board numbering is not a continuous list from project_creator.1-{highest_board_number}. "
                    "Aborting.",
                    "Unexpected board numbering",
                )
            board_number = highest_board_number + 1
            self.logger.info(
                f"{len(existing_boards)} existing board found. Creating board number {board_number:03d}"
            )
        else:
            board_number = 1
            self.logger.info(
                f"No boards found. Creating board number {board_number:03d}"
            )
        return board_number

    def get_project_number(self, hardware_folder_path: Path) -> int:
        git_info = get_git_info(hardware_folder_path.parent)
        project_number_match = re.search(r"p(\d{4})_", git_info.upstream)

        if project_number_match is None:
            show_error(
                "Upstream repo does not match pattern of M0WUT project handler",
                "Unsupported repo name",
            )

        project_number = int(project_number_match.group(1))  # type: ignore
        self.logger.info(f"Upstream repo detected as P{project_number:04d}")
        return project_number

    def _validate_board_name(self, x: str) -> bool:
        return bool(re.fullmatch(r"(?=.*[A-Za-z0-9])[A-Za-z0-9 ]+", x))

    def get_board_name(
        self, board_id: str, existing_board_names: list[str]
    ) -> tuple[str, str]:
        while True:
            requested_board_name = get_text_input(
                message=(
                    "Please enter requested board name as it would be written in a document.\n"  # noqa:E501
                    'e.g. "Awesome Board" rather than "awesome_board" or "awesome-board".\n'  # noqa:E501
                    "It will be correctly formatted later to be compatible with Github and to avoid spaces in folder names."  # noqa:E501
                ),
                title=f"Enter board name for {board_id}",
            )

            if self._validate_board_name(requested_board_name) is False:
                show_error(
                    "Board name must only contain letters (any case) and spaces",
                    "Invalid name",
                    exit_on_error=False,
                )
                continue

            if requested_board_name in existing_board_names:
                show_error(
                    f'Board "{requested_board_name}" already exists',
                    "Board name already exists",
                    exit_on_error=False,
                )
                continue

            self.logger.info(f'Accepted board name "{requested_board_name}"')

            github_sanitised_repo_name = re.sub(" ", "-", requested_board_name.lower())
            repo_name = f"{board_id.lower()}_{github_sanitised_repo_name}"

            return requested_board_name, repo_name

    def update_board_tracker(
        self,
        board_tracker_path: Path,
        board_number: int,
        board_id: str,
        board_name: str,
        repo_name: str,
    ) -> None:
        with open(board_tracker_path, "a+") as boards_file:
            boards_file.write(
                f'{board_number:03d},{board_id},"{board_name}",'
                f"https://github.com/{self.gh_user}/{repo_name}\n"
            )

        # self.update_project_tracker_readme()

        # git_commit_and_push(
        #     self.project_tracker_clone_path,
        #     f"Added project number {project_number}",
        # )

    def create_new_project(self):

        hardware_folder_path = self.select_local_hardware_folder()
        project_path = hardware_folder_path.parent
        board_tracker_path = hardware_folder_path / "boards.csv"

        project_number = self.get_project_number(hardware_folder_path)
        board_number = self.generate_next_board_number(board_tracker_path)
        board_id = f"P{project_number:04d}-{board_number:03d}"

        existing_board_names = [
            x[1] for x in self.get_board_tracker_info(board_tracker_path)
        ]

        self.logger.info(f"Creating board number {board_id}")

        board_name, repo_name = self.get_board_name(board_id, existing_board_names)

        self.logger.info(f'Creating blank Github repo "{self.gh_user}/{repo_name}')
        create_blank_github_repo(f"{self.gh_user}/{repo_name}")

        self.logger.info("Updating Board Tracker")
        self.update_board_tracker(
            board_tracker_path,
            board_number,
            board_id,
            board_name,
            repo_name,
        )

        kicad_project_path = hardware_folder_path / repo_name

        git_clone(self.gh_user, repo_name, kicad_project_path)

        with open(kicad_project_path / "README.md", "w+") as readme_file:
            readme_file.write(f"# {board_id} - {board_name}")

        git_commit_and_push(kicad_project_path, "Added README")
        git_commit_and_push(project_path, f"Added board {board_id}")


if __name__ == "__main__":
    import wx

    _ = wx.App()
    x = KicadProjectHandler("M0WUT")
    x.create_new_project()
