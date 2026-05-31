# Standard imports
from pathlib import Path
import re

# Third party imports

# Local imports
from argonaut.gui.dialog import show_info
from argonaut.misc.git import (
    generate_github_repo_url,
    git_clone_interactive,
    git_commit_and_push,
)
from argonaut.config.config import (
    PROJECT_TRACKER_REPO_OWNER,
    PROJECT_TRACKER_REPO_NAME,
    PROJECT_TRACKER_JSON_PATH,
)
from argonaut.creator.creator import Creator
from argonaut.tracker.project_tracker import ProjectTracker


class ProjectCreator(Creator):

    @classmethod
    def format_project_number_str(cls, project_number: int) -> str:
        return f"P{project_number:04d}"

    @classmethod
    def is_valid_project_repo_name(cls, name: str) -> bool:
        """
        Takes a candiate Github repo name and returns True
        if it matches the format that this tool creates
        """
        pattern = re.compile(r"^p\d{4}-\d{3}_[a-z]+(?:-[a-z]+)*$")
        return pattern.fullmatch(name) is not None

    def run(self):
        self.repo_owner = PROJECT_TRACKER_REPO_OWNER
        self.repo_name = PROJECT_TRACKER_REPO_NAME
        self.json_path = PROJECT_TRACKER_JSON_PATH
        self.item_name = "project"

        self.tracker = self.context_manager_stack.enter_context(
            ProjectTracker(self.repo_owner, self.repo_name, self.json_path)
        )

        self.project_number = self.tracker.generate_next_project_number()
        self.reference = self.format_project_number_str(self.project_number)
        self.logger.info(f"Assigned project {self.reference}")

        self.create_repo()

        self.logger.info("Repo created, cloning to local machine")
        self.local_clone_path = git_clone_interactive(
            self.repo_owner,
            self.repo_name,
            f"{self.reference}_{self.name.title().replace(' ', '')}",
        )
        self.logger.info(f"Cloned successfully to {self.local_clone_path.absolute()}")

        self.add_basic_readme()
        git_commit_and_push(self.local_clone_path, "added README")
        self.logger.info("Added README")

        self.tracker.update(
            self.reference,
            self.name,
            self.description,
            generate_github_repo_url(self.repo_owner, self.repo_name),
        )

        show_info(
            "Successfully created project\n"
            f"Project number: {self.reference}\n"
            f"Project name: {self.name}\n"
            f"Description: {self.description}\n"
            f"Github repo: {self.repo_owner}/{self.repo_name}\n"
            f"Local clone: {self.local_clone_path.absolute()}",
            "Project creation complete",
        )

    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return f"{self.reference.lower()}_{github_sanitised_repo_name}"

    def add_basic_readme(self):
        readme_path = self.local_clone_path / "README.md"
        self._add_readme_header(readme_path)

    def _add_readme_header(self, readme_path: Path):
        with open(readme_path, "w+") as readme_file:
            readme_file.write(f"# {self.reference} - {self.name}\n")
            readme_file.write(f"{self.description}\n")
