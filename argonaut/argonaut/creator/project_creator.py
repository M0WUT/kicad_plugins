# Standard imports
from pathlib import Path
import re
import json

# Third party imports

# Local imports
from argonaut.templates.pcb_template import create_pcb_readme_table
from argonaut.config.supported_document_types import SUPPORTED_DOCUMENT_TYPES
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
    PROJECT_JSON_PATH,
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
        pattern = re.compile(r"^p\d{4}_[a-z]+(?:-[a-z]+)*$")
        return pattern.fullmatch(name) is not None

    def run(self):
        self.repo_owner = PROJECT_TRACKER_REPO_OWNER
        self.json_path = PROJECT_TRACKER_JSON_PATH
        self.item_name = "project"

        self.tracker = self.context_manager_stack.enter_context(
            ProjectTracker(self.repo_owner, PROJECT_TRACKER_REPO_NAME, self.json_path)
        )

        self.project_number = self.tracker.generate_next_number()
        self.reference = self.format_project_number_str(self.project_number)
        self.logger.info(f"Assigned project {self.reference}")

        self.create_repo()
        self.url = generate_github_repo_url(self.repo_owner, self.repo_name)

        self.logger.info("Repo created, cloning to local machine")
        self.local_clone_path = git_clone_interactive(
            self.repo_owner,
            self.repo_name,
            f"{self.reference}_{self.name.title().replace(' ', '')}",
        )
        self.logger.info(f"Cloned successfully to {self.local_clone_path.absolute()}")

        self.add_basic_project_json()
        regenerate_project_readme(self.local_clone_path)
        git_commit_and_push(self.local_clone_path, "added README")
        self.logger.info("Added README")

        self.url

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

    def add_basic_project_json(self):
        json_info = {
            "reference": self.reference,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "documents": {},
        }
        with open(self.local_clone_path / PROJECT_JSON_PATH, "w+") as file:
            json.dump(json_info, file, indent=4)


def regenerate_project_readme(local_project_root: Path):

    with open(local_project_root / PROJECT_JSON_PATH, "r") as file:
        info = json.load(file)

    readme_path = local_project_root / "README.md"
    with open(readme_path, "w+") as readme_file:
        readme_file.write(f"# {info['reference']} - {info['name']}\n")
        readme_file.write(f"{info['description']}\n")

        for doc_type in SUPPORTED_DOCUMENT_TYPES:

            try:
                pass
                docs = info["documents"][doc_type.abbreviation.lower()]
                readme_file.write(f"## {doc_type.description}s\n")
                if doc_type.abbreviation == "PCB":
                    create_pcb_readme_table(readme_file, docs)
                else:
                    # Generic handler
                    readme_file.write("| Reference | Name | Description | URL |\n")
                    readme_file.write("| --- | --- | --- | --- |\n")
                    for doc_reference, doc in docs.items():
                        readme_file.write(
                            f"| {doc_reference} | {doc['name']} | {doc['description']} | {doc['url']} |\n"  # noqa: E501
                        )
            except KeyError:
                pass
