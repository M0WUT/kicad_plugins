import logging
from pathlib import Path
import re
import csv
from typing import Optional


from .github_helper import (
    create_blank_github_repo,
    check_github_project_exists,
    git_checkout,
    git_push,
)
from .os_functions import delete_folder, get_temp_path
from .ui import (
    get_text_input,
    show_error,
    show_info,
)
from .config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    TEMP_FOLDER_NAME,
)
from .logging_handler import configure_logger


class ProjectHandler:
    """
    Class for handling operations at the Project (i.e. a super repo relating to a single
    'product' development that may contain multiple hardware / software / misc repos)
    """

    def __init__(self, gh_user: str):
        self.gh_user = gh_user
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)
        self.project_tracker_checkout_path: Optional[Path] = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.project_tracker_checkout_path is not None:
            delete_folder(self.project_tracker_checkout_path)
            self.project_tracker_checkout_path = None

    def ensure_project_tracker_repo_exists(self):
        """
        Ensures there's a checkout of the project tracker repo
        If this has already been checked out, this will do nothing.
        Otherwise, it will checkout the project tracker repo
        """
        # Early return if already present
        if self.project_tracker_checkout_path is not None:
            return

        self.project_tracker_checkout_path = (
            get_temp_path() / TEMP_FOLDER_NAME / "project-tracker"
        )

        self.project_tracker_checkout_path.mkdir(parents=True, exist_ok=True)

        check_github_project_exists(self.gh_user, PROJECT_NUMBER_TRACKER_REPO_NAME)
        self.logger.info(
            "Using project tracker repo "
            f'"{self.gh_user}/{PROJECT_NUMBER_TRACKER_REPO_NAME}"'
        )

        self.logger.info(
            "Checking out project tracker repo to "
            f'"{self.project_tracker_checkout_path.absolute()}"'
        )
        git_checkout(
            self.gh_user,
            PROJECT_NUMBER_TRACKER_REPO_NAME,
            self.project_tracker_checkout_path,
        )
        self.logger.info("Checkout successful")

    def get_project_tracker_info(self) -> list[list[str]]:
        self.ensure_project_tracker_repo_exists()
        try:
            with open(
                self.project_tracker_checkout_path / "projects.csv", "r"
            ) as projects_file:
                project_tracker_reader = csv.reader(
                    projects_file, quotechar='"', delimiter=","
                )
                existing_projects = [x for x in project_tracker_reader]
            self.logger.info(f"Loaded info on {len(existing_projects)} projects")
            return existing_projects
        except FileNotFoundError:
            self.logger.warning("Project tracking csv not found. Creating blank file")
            return []

    def generate_next_project_number(self) -> int:
        existing_projects = self.get_project_tracker_info()

        if existing_projects:
            highest_project_number = int(existing_projects[-1][0])
            if highest_project_number != len(existing_projects):
                show_error(
                    "Highest project number is not the same as the number of projects. "
                    "Aborting.",
                    "Unexpected project numbering",
                )
            project_number = highest_project_number + 1
            self.logger.info(
                f"{len(existing_projects)} existing projects found. Next available "
                f"project number is P{project_number:04d}"
            )
        else:
            project_number = 1
            self.logger.info(f"No projects found. Starting with P{project_number:04d}")
        return project_number

    def update_project_tracker(
        self,
        project_number: int,
        project_name: str,
        project_description: str,
        repo_name: str,
    ):
        with open(
            self.project_tracker_checkout_path / "projects.csv", "a+"
        ) as projects_file:
            projects_file.write(
                f'{project_number},"{project_name}","{project_description}",'
                f"https://github.com/{self.gh_user}/{repo_name}\n"
            )

        self.update_readme()

        git_push(
            self.project_tracker_checkout_path,
            f"Added project number {project_number}",
        )

        self.logger.info("Successfully updated project tracker")

    def create_new_project(self) -> None:

        project_number = self.generate_next_project_number()
        project_name, repo_name = self.get_project_name(
            project_number,
            existing_project_names=[x[1] for x in self.get_project_tracker_info()],
        )

        self.logger.info(f'Using Github repo: "{self.gh_user}/{repo_name}"')

        if check_github_project_exists(
            self.gh_user, repo_name, show_error_window=False
        ):
            show_error(
                f'Cannot create new Github repo "{self.gh_user}/{repo_name}. '
                "It already exists",
                "Repo already exists",
            )

        create_blank_github_repo(f"{self.gh_user}/{repo_name}")

        project_description = self.get_project_description()

        # Update the tracker
        self.update_project_tracker(
            project_number, project_name, project_description, repo_name
        )

        show_info(
            "Successfully created project\n"
            f"Project number: P{project_number:04d}\n"
            f"Project name: {project_name}\n"
            f"Github repo: {self.gh_user}/{repo_name}",
            "Project creation complete",
        )

    def _validate_str(self, x: str) -> bool:
        if re.fullmatch(r"(?=.*[A-Za-z0-9])[A-Za-z0-9 ]+", x):
            return True
        else:
            return False

    def get_project_name(
        self, project_number: int, existing_project_names: list[str]
    ) -> tuple[str, str]:
        while True:
            requested_project_name = get_text_input(
                message=(
                    "Please enter requested project name as it would be written in a document.\n"  # noqa:E501
                    'e.g. "Awesome Project" rather than "awesome_project" or "awesome-project".\n'  # noqa:E501
                    "It will be correctly formatted later to be compatible with Github and to avoid spaces in folder names."  # noqa:E501
                ),
                title=f"Enter project name for P{project_number:04d}",
            )

            if self._validate_str(requested_project_name) is False:
                show_error(
                    "Project name must only contain letters (any case) and spaces",
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

            self.logger.info(f'Accepted project name "{requested_project_name}"')

            github_sanitised_repo_name = re.sub(
                " ", "-", requested_project_name.lower()
            )
            repo_name = f"p{project_number:04d}_{github_sanitised_repo_name}"

            return requested_project_name, repo_name

    def get_project_description(self) -> str:
        while True:
            project_description = get_text_input(
                "Please enter project description", "Enter project description"
            )
            if '"' in project_description:
                show_error(
                    'Project description must not contain speech marks (")',
                    "Invalid description",
                    exit_on_error=False,
                )
                continue
            self.logger.info(f'Accepted project description "{project_description}"')
            return project_description

    def update_readme(self) -> None:
        with open(self.project_tracker_checkout_path / "README.md", "w+") as readme:
            readme.write("# M0WUT Project tracker\n")
            readme.write("| Project number | Project name | Description | URL |\n")
            readme.write("| --- | --- | --- | --- |\n")
            self.logger.info(self.get_project_tracker_info())
            for number, name, des, url in self.get_project_tracker_info():
                readme.write(f"| {number} | {name} | {des} | [Main Repo]({url})\n")
