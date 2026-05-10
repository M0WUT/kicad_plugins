# Standard imports
from dataclasses import dataclass
import logging
import sys
from typing import Optional

# Third party imports

# Local imports
from .git_functions import (
    check_github_repo_exists,
    create_blank_github_repo,
)
from .repo_tracker import RepoTracker
from .ui import ask_question, get_text_input, show_error


@dataclass
class Creator:
    board_repo_owner: str
    board_repo_name: str
    item_name: str
    logger: logging.Logger
    _tracker: Optional[RepoTracker] = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self._tracker is not None:
            self._tracker.__exit__()

    def input_item_name(self, title: str):
        while True:
            name = get_text_input(
                message=(
                    f"Please enter requested {self.item_name.lower()} name as it would be written in a document.\n"  # noqa:E501
                    f'e.g. "Awesome {self.item_name.title()}" rather than "awesome_{self.item_name.lower()}" or "awesome-{self.item_name.lower()}".\n'  # noqa:E501
                    "It will be correctly formatted later to be compatible with Github and to avoid spaces in folder names."  # noqa:E501
                ),
                title=title,
            )
            if self._tracker.validate_item_name(name):
                # validate_item_name will show error box
                # detailing what is wrong with the proposed name
                break
        return name

    def input_item_description(self) -> str:
        while True:
            description = get_text_input(
                f"Please enter {self.item_name.lower()} description",
                f"Enter {self.item_name.lower()} description",
            )
            if '"' in description:
                show_error(
                    f'{self.item_name.title()} description must not contain speech marks (")',  # noqa: E501
                    "Invalid description",
                    exit_on_error=False,
                )
                continue
            else:
                break
        self.logger.info(f'Accepted description of "{description}"')
        return description

    @classmethod
    def format_item_number(cls, number: int):
        raise NotImplementedError

    def generate_repo_name(self) -> str:
        raise NotImplementedError

    def create_new_repo(self):
        self.number = self._tracker.generate_next_item_number()
        self.logger.info(
            f"Attempting to create {self.item_name.lower()} number "
            f"{self.format_item_number(self.number)}"
        )
        self.name = self.input_item_name(
            f"Enter name for {self.item_name.lower()} "
            f"{self.format_item_number(self.number)}"
        )

        self.board_repo_name = self.generate_repo_name()

        if check_github_repo_exists(
            self.board_repo_owner,
            self.board_repo_name,
            show_error_window_if_not_exists=False,
        ):
            # Given that the project number and name should be unique for this user
            # if we get here, the tracker is not accurately reflecting the created
            # repositories so abort as something has gone wrong somewhere
            show_error(
                "Cannot create new Github repo "
                f'"{self.board_repo_owner}/{self.board_repo_name}. '
                "It already exists",
                "Repo already exists",
            )

        self.logger.info(
            f'Using Github repo: "{self.board_repo_owner}/{self.board_repo_name}"'
        )

        self.description = self.input_item_description()

        if (
            ask_question(
                "Is it OK to create the Github project "
                f'"{self.board_repo_owner}/{self.board_repo_name}" '
                f'with the description "{self.description}"?',
                "Confirm Github project details",
            )
            is False
        ):
            sys.exit(0)

        create_blank_github_repo(f"{self.board_repo_owner}/{self.board_repo_name}")
