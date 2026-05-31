# Standard imports
from pathlib import Path
import re

# Third party imports

# Local imports
from project_creator.creators.repo_creator import RepoCreator
from project_creator.trackers.project_tracker import ProjectTracker
from argonaut.argonaut.misc.git import (
    generate_github_repo_url,
    git_clone_interactive,
    git_commit_and_push,
)
from argonaut.argonaut.gui.ui import (
    show_info,
)
from config import PROJECT_NUMBER_TRACKER_REPO_NAME


class ProjectCreator(RepoCreator):
    """
    Class for handling operations at the Project (i.e. a super repo relating to a single
    'product' development that may contain multiple hardware / software / misc repos)
    """

    def create_tracker(self):
        return ProjectTracker(self.repo_owner, PROJECT_NUMBER_TRACKER_REPO_NAME)

    @classmethod
    def format_item_number(cls, number: int):
        return f"P{number:04d}"

    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return f"p{self.number:04d}_{github_sanitised_repo_name}"

    def create_new_project(self) -> None:
        assert self.tracker is not None
        self.create_new_repo()
        self.project_number = self.number
        self.project_name = self.name
        self.project_description = self.description

        # Update the tracker
        self.tracker.update_tracker_repo(
            self.project_number,
            self.project_name,
            [
                self.project_description,
                generate_github_repo_url(self.repo_owner, self.repo_name),
            ],
        )

        self.logger.info("Cloning project to local machine")

        self.local_folder = git_clone_interactive(
            self.repo_owner,
            self.repo_name,
            f"P{self.project_number:04d}_{self.project_name.title().replace(' ', '')}",
        )
        self.logger.info("Clone successful")

        self.logger.info("Adding README.md")
        self.add_basic_readme()
        git_commit_and_push(self.local_folder, "added README")

        show_info(
            "Successfully created project\n"
            f"Project number: P{self.project_number:04d}\n"
            f"Project name: {self.project_name}\n"
            f"Description: {self.project_description}\n"
            f"Github repo: {self.repo_owner}/{self.repo_name}\n"
            f"Local clone: {self.local_folder.absolute()}",
            "Project creation complete",
        )
