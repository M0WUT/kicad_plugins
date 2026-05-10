# Standard imports
import logging
from pathlib import Path
import re

# Third party imports

# Local imports
from .creator import Creator
from .repo_tracker import ProjectTracker
from .git_functions import (
    git_clone_interactive,
    git_commit_and_push,
)
from .ui import (
    show_info,
)
from .logging_handler import configure_logger


class ProjectCreator(Creator):
    """
    Class for handling operations at the Project (i.e. a super repo relating to a single
    'product' development that may contain multiple hardware / software / misc repos)
    """

    def __init__(self, tracker_repo_owner: str, tracker_repo_name: str):
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)
        super().__init__(tracker_repo_owner, tracker_repo_name, "project", self.logger)
        self._tracker = ProjectTracker(tracker_repo_owner, tracker_repo_name)

    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return f"p{self.number:04d}_{github_sanitised_repo_name}"

    @classmethod
    def format_item_number(cls, number: int):
        return f"P{number:04d}"

    def add_project_readme_header(self, readme_path: Path):
        with open(readme_path, "w+") as readme_file:
            readme_file.write(f"# P{self.project_number:04d} - {self.project_name}\n")
            readme_file.write(f"{self.project_description}\n")

    def add_basic_project_readme(self):
        readme_path = self.local_folder / "README.md"
        self.add_project_readme_header(readme_path)
        git_commit_and_push(self.local_folder, "added README")

    def create_new_project(self) -> None:
        self.create_new_repo()
        self.project_number = self.number
        self.project_name = self.name
        self.project_description = self.description

        # Update the tracker
        self._tracker.update_tracker_repo(
            self.project_number,
            self.project_name,
            [
                self.project_description,
                f"https://github.com/{self.board_repo_owner}/{self.board_repo_name}",
            ],
        )

        self.logger.info("Cloning project to local machine")

        self.local_folder = git_clone_interactive(
            self.board_repo_owner,
            self.board_repo_name,
            f"P{self.project_number:04d}_{self.project_name.title().replace(' ', '')}",
        )
        self.logger.info("Clone successful")

        self.logger.info("Adding README.md")
        self.add_basic_project_readme()

        show_info(
            "Successfully created project\n"
            f"Project number: P{self.project_number:04d}\n"
            f"Project name: {self.project_name}\n"
            f"Description: {self.project_description}\n"
            f"Github repo: {self.board_repo_owner}/{self.board_repo_name}\n"
            f"Local clone: {self.local_folder.absolute()}",
            "Project creation complete",
        )
