# Standard imports
from contextlib import suppress
from dataclasses import dataclass
import logging
from pathlib import Path
import sys

from argonaut.argonaut.logger.logger import configure_logger

# Third party imports

# Local imports
from argonaut.argonaut.misc.git import (
    check_github_repo_exists,
    create_blank_github_repo,
    get_git_info,
)
from project_creator.trackers.repo_tracker import RepoTracker
from argonaut.gui.ui import ask_question, get_text_input, show_error


class RepoCreator:
    def __init__(self, repo_owner: str):
        self.project_path = None
        self.repo_owner = repo_owner
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.INFO)
        self.tracker: RepoTracker = self.create_tracker()
        self.item_name = self.tracker.get_item_name()

        # This should have been set when creating tracker
        assert self.project_path is not None
        # Copy some stuff to more helpfully named variables
        self.project_git_info = get_git_info(self.project_path)
        self.repo_owner = self.project_git_info.repo_owner
        self.project_repo_name = self.project_git_info.repo_name
        self.project_number = int(self.project_git_info.repo_name[1:5])

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        with suppress(AttributeError):
            if self.tracker is not None:
                self.tracker.__exit__()

    def create_tracker(self) -> RepoTracker:
        raise NotImplementedError

    @classmethod
    def format_item_number(cls, number: int):
        raise NotImplementedError

    def generate_repo_name(self) -> str:
        raise NotImplementedError

    def create_new_repo(self):
        self.number = self.tracker.generate_next_item_number()
        self.logger.info(
            f"Attempting to create {self.item_name.lower()} number "
            f"{self.format_item_number(self.number)}"
        )
        self.name = self.input_item_name(
            f"Enter name for {self.item_name.lower()} "
            f"{self.format_item_number(self.number)}"
        )

        self.repo_name = self.generate_repo_name()

        if check_github_repo_exists(
            self.repo_owner,
            self.repo_name,
            show_error_window_if_not_exists=False,
        ):
            # Given that the project number and name should be unique for this user
            # if we get here, the tracker is not accurately reflecting the created
            # repositories so abort as something has gone wrong somewhere
            show_error(
                "Cannot create new Github repo "
                f'"{self.repo_owner}/{self.repo_name}. '
                "It already exists",
                "Repo already exists",
            )

        self.logger.info(f'Using Github repo: "{self.repo_owner}/{self.repo_name}"')

        self.description = self.input_item_description()

        if (
            ask_question(
                "Is it OK to create the Github project "
                f'"{self.repo_owner}/{self.repo_name}" '
                f'with the description "{self.description}"?',
                "Confirm Github project details",
            )
            is False
        ):
            sys.exit(0)

        create_blank_github_repo(f"{self.repo_owner}/{self.repo_name}")

    def add_basic_readme(self):
        raise NotImplementedError

    def _add_readme_header(self, readme_path: Path):
        raise NotImplementedError
