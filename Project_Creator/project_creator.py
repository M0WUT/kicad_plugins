from contextlib import suppress
import logging
import re
import csv

import wx

from .github_helper import (
    create_blank_github_repo,
    github_cli_exists,
    github_project_exists,
    get_current_github_user,
    git_checkout,
    git_push,
)
from .os_functions import delete_folder, get_temp_path
from .ui import (
    get_folder_input,
    get_text_input,
    show_error,
    show_info,
)
from .config import (
    BOARD_TRACKER_PROJECT_USER,
    BOARD_TRACKER_REPO,
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    TEMP_FOLDER_NAME,
)
from .logging_handler import configure_logger


class ProjectCreator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)
        self.validate_github_settings()
        self.generate_project_number_and_name()

    def validate_github_settings(self):
        # Check if Github CLI is present
        if github_cli_exists():
            self.logger.info("Github CLI found")
        else:
            show_error(
                "Github CLI not found. Please ensure it is installed",
                "Github CLI not found",
            )

        # Query for Github user
        self.gh_user = get_current_github_user()
        if self.gh_user is None:
            show_error(
                "Github CLI is not authenticated as a user",
                "Github CLI not authenticated",
            )

        self.logger.info(f"Github user detected as {self.gh_user}")

    def generate_project_number_and_name(self) -> int:
        temp_checkout_path = None
        try:
            # Checkout tracker repo
            temp_checkout_path = get_temp_path() / TEMP_FOLDER_NAME / "project-tracker"
            temp_checkout_path.mkdir(parents=True, exist_ok=True)

            if github_project_exists(self.gh_user, PROJECT_NUMBER_TRACKER_REPO_NAME):
                self.logger.info(
                    f'Using project tracker repo "{self.gh_user}/{PROJECT_NUMBER_TRACKER_REPO_NAME}"'
                )
            else:
                show_error(
                    f'Project tracker repo "{self.gh_user}/{PROJECT_NUMBER_TRACKER_REPO_NAME}" does not exist',
                    "Project tracker repo not found",
                )

            self.logger.info(
                f'Checking out project tracker repo to "{temp_checkout_path.absolute()}"'
            )
            git_checkout(
                self.gh_user,
                PROJECT_NUMBER_TRACKER_REPO_NAME,
                temp_checkout_path,
            )

            # Extract previous project numbers
            existing_projects = []
            existing_project_names = []
            with suppress(FileNotFoundError):
                with open(temp_checkout_path / "projects.csv", "r") as projects_file:
                    project_tracker_reader = csv.reader(
                        projects_file, quotechar='"', delimiter=","
                    )
                    existing_projects = [x for x in project_tracker_reader]
                existing_project_names = [x[1] for x in existing_projects]

            if existing_projects:
                highest_project_number = int(existing_projects[-1][0])
                if highest_project_number != len(existing_projects):
                    show_error(
                        "Highest project number is not the same as the number of projects. Aborting.",
                        "Unexpected project numbering",
                    )
                self.project_number = highest_project_number + 1
                self.logger.info(
                    f"{len(existing_projects)} existing projects found. Next available project number is P{self.project_number:04d}"
                )
            else:
                self.project_number = 1
                self.logger.info(
                    f"No projects found. Starting with P{self.project_number:04d}"
                )

            self.get_project_name(existing_project_names)
            github_sanitised_repo_name = re.sub(" ", "-", self.project_name.lower())
            self.repo_name = f"p{self.project_number:04d}_{github_sanitised_repo_name}"
            self.logger.info(f'Using Github repo: "{self.gh_user}/{self.repo_name}"')

            if github_project_exists(self.gh_user, self.repo_name):
                show_error(
                    f"Github repo: {self.gh_user}/{self.repo_name} already exists. Aborting",
                    "Repo already exists",
                )

            # Create blank repo
            if create_blank_github_repo(f"{self.gh_user}/{self.repo_name}"):
                self.logger.info("Repo created successfully")
            else:
                show_error("Project repo creation failed", "Repo creation failed")

            # Update the tracker
            with open(temp_checkout_path / "projects.csv", "a+") as projects_file:
                projects_file.write(f'{self.project_number},"{self.project_name}"\n')

            git_push(temp_checkout_path, f"Added project number {self.project_number}")

            self.logger.info("Successfully updated project tracker")

        finally:
            if temp_checkout_path is not None:
                delete_folder(temp_checkout_path)

        show_info(
            f"Successfully created project\nProject number: P{self.project_number:04d}\nProject name: {self.project_name}\nGithub repo: {self.gh_user}/{self.repo_name}",
            "Project creation complete",
        )

    def get_project_name(self, existing_project_names: list[str]) -> None:
        self.project_name = ""
        while self.project_name == "":
            requested_project_name = get_text_input(
                message=(
                    "Please enter requested project name as it would be written in a document.\n"
                    'e.g. "Awesome Project" rather than "awesome_project" or "awesome-project".\n'
                    "It will be correctly formatted later to be compatible with Github and to avoid spaces in folder names."
                ),
                title=f"Enter project name for P{self.project_number:04d}",
            )

            if not re.fullmatch(
                r"(?=.*[A-Za-z0-9])[A-Za-z0-9 ]+", requested_project_name
            ):
                show_error(
                    "Project name must only contain upper/lower case letters and spaces",
                    "Invalid name",
                    exit_on_error=False,
                )
                continue

            if requested_project_name in existing_project_names:
                show_error(
                    f'Project "{requested_project_name}" already exists',
                    "Repo already exists",
                    exit_on_error=False,
                )
                continue

            # Project name has been validated - save it
            self.project_name = requested_project_name
            self.logger.info(f'Accepted project name "{self.project_name}"')


def run():
    _ = ProjectCreator()


if __name__ == "__main__":
    _ = wx.App()
    run()
