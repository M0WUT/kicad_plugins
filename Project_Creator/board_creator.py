import logging
from pathlib import Path
import re
import csv
import sys
from typing import Optional

from git import InvalidGitRepositoryError

from creator import Creator

from repo_tracker import BoardTracker


from git_functions import (
    copy_files_from_git_repo,
    ensure_git_repo_up_to_date,
    get_git_info,
    git_add_explicit_path,
    git_commit_and_push,
    create_blank_github_repo,
    check_github_repo_exists,
    git_clone,
    git_pull,
    git_pull_including_submodules,
    validate_github_setup,
)

from os_functions import copy_into, delete_folder, get_temp_dir_path
from ui import (
    ask_question,
    get_folder_input,
    get_text_input,
    show_error,
    show_info,
    show_warning,
)
from config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    RELEASER_PROJECT_REPO_NAME,
    RELEASER_PROJECT_REPO_OWNER,
    TEMP_FOLDER_NAME,
    TEMPLATE_PROJECT_REPO_NAME,
    TEMPLATE_PROJECT_REPO_OWNER,
)
from logging_handler import configure_logger


class BoardCreator(Creator):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)
        self.hardware_folder_path = self.select_local_hardware_folder()
        self.project_path = self.hardware_folder_path.parent
        self.project_git_info = get_git_info(self.project_path)

        self.logger.info(f'Detected repo "{self.project_git_info.upstream}"')
        self.project_repo_owner = self.project_git_info.github_repo_owner
        self.project_repo_name = self.project_git_info.github_repo_name

        # First 5 characters of repo name should be pxxxx
        # where xxxx is zero-padded project number
        try:
            self.project_number = int(self.project_git_info.github_repo_name[1:5])
        except ValueError:
            show_error(
                f'Detected repo "{self.project_git_info.upstream}" does not appear '
                "to be managed by M0WUT kicad plugins",
                "Unsupported repo",
            )
        self.logger.info(f"Detected project P{self.project_number:04d}")

        super().__init__(
            self.project_repo_owner, self.project_repo_name, "board", self.logger
        )
        # The tracker for boards should be in the project repo
        self._tracker = BoardTracker(self.project_repo_owner, self.project_repo_name)

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

    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return (
            f"p{self.project_number:04d}-{self.number:03d}_{github_sanitised_repo_name}"
        )

    @classmethod
    def format_item_number(cls, number: int):
        return f"{number:03d}"

    def create_new_project(self):
        self.create_new_repo()
        self.board_number = self.number
        self.board_name = self.name
        self.board_description = self.description

        self.board_id = f"P{self.project_number:04d}-{self.board_number:03d}"

        kicad_project_path = (
            self._tracker.local_clone_path
            / "hardware"
            / f"{self.board_id}_{self.board_name.title().replace(' ', '')}"
        )

        git_clone(self.project_repo_owner, self.project_repo_name, kicad_project_path)

        with open(kicad_project_path / "README.md", "w+") as readme_file:
            readme_file.write(f"# {self.board_id} - {self.board_name}")

        # These must be this way round as the submodule needs a commit for the
        # parent to

        # Want to update board tracker as fast as possible, even though we're going to do more to the
        # board folder
        git_commit_and_push(kicad_project_path, "Added README")
        git_commit_and_push(
            self._tracker.local_clone_path, f"Added board {self.board_id} to tracker"
        )

        self._tracker.update_tracker_repo(
            self.board_number,
            self.board_name,
            [
                self.board_description,
                self.board_id,
                f"https://github.com/{self.project_repo_owner}/{self.project_repo_name}",
                f"https://{self.project_repo_owner}.github.io/{self.project_repo_name}",
            ],
        )

        # Get template project files
        copy_files_from_git_repo(
            TEMPLATE_PROJECT_REPO_OWNER,
            TEMPLATE_PROJECT_REPO_NAME,
            kicad_project_path,
            exclude_paths=[Path("README.md")],
        )

        # Rename files
        for file in kicad_project_path.rglob(f"{TEMPLATE_PROJECT_REPO_NAME}*"):
            file.rename(file.parent / f"{self.board_id}{file.suffix}")

        # Replace text content in files
        for path in kicad_project_path.rglob("*"):
            if path.is_file():
                try:
                    text = path.read_text(encoding="utf-8")
                    path.write_text(
                        text.replace(TEMPLATE_PROJECT_REPO_NAME, self.board_name),
                        encoding="utf-8",
                    )
                except UnicodeDecodeError:
                    print(f"Not a text file: {path}")

        # Copy Github actions folder
        copy_files_from_git_repo(
            RELEASER_PROJECT_REPO_OWNER,
            RELEASER_PROJECT_REPO_NAME,
            kicad_project_path,
            include_paths=[Path("github")],
        )
        (kicad_project_path / "github").rename(kicad_project_path / ".github")
        git_commit_and_push(kicad_project_path, "Added template files")

        git_commit_and_push(
            self._tracker.local_clone_path,
            f"Added template board files for {self.board_id}",
        )

        # Finally git pull on the local folder
        git_pull(self.project_path)


if __name__ == "__main__":
    import wx

    _ = wx.App()
    with BoardCreator() as x:
        x.create_new_project()
