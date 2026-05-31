# Standard imports
from contextlib import ExitStack
import re
import sys
from typing import Optional

# Third party imports
import wx

# Local imports
from argonaut.misc.git import check_github_repo_exists, create_blank_github_repo
from argonaut.gui.dialog import ask_question, get_text_input, show_error
from argonaut.logger.logger import create_default_logger


class Creator:

    MAX_NAME_LENGTH = 32

    def __init__(self, parent_frame: wx.Frame):
        self.parent_frame = parent_frame

        self.logger = create_default_logger(__name__)
        self.tracker = None
        self.context_manager_stack = ExitStack()
        self.item_name: Optional[str] = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.context_manager_stack.close()

    def input_name(self, title: str) -> str:
        assert self.item_name is not None
        while True:
            name = get_text_input(
                message=(
                    f"Please enter requested {self.item_name.lower()} name as it would be written in a document.\n"  # noqa:E501
                    f'e.g. "Awesome {self.item_name.title()}" rather than "awesome_{self.item_name.lower()}" or "awesome-{self.item_name.lower()}".\n'  # noqa:E501
                    "It will be correctly formatted later to be compatible with Github and to avoid spaces in folder names."  # noqa:E501
                ),
                title=title,
            )
            if self.validate_item_name(name):
                # validate_item_name will show error box
                # detailing what is wrong with the proposed name
                break
        self.logger.info(f"Accepted name: {name}")
        return name

    def input_description(self) -> str:
        while True:
            description = get_text_input(
                f"Please enter {self.item_name.lower()} description",
                f"Enter {self.item_name.lower()} description",
            )
            if description == "":
                continue

            if '"' in description:
                show_error(
                    f'{self.item_name.title()} description must not contain speech marks (")',  # noqa: E501
                    "Invalid description",
                    exit_on_error=False,
                )
                continue
            else:
                break
        self.logger.info(f"Accepted description: {description}")
        return description

    def validate_name(self, x: str) -> bool:
        return bool(re.fullmatch(r"[A-Za-z0-9]+(?: [A-Za-z0-9]+)*", x))

    def validate_item_name(self, name: str):
        if not self.validate_name(name):
            show_error(
                f"Suggested {self.item_name} name contains invalid characters",
                "Invalid characters",
                False,
            )
            return False
        if len(name) > self.MAX_NAME_LENGTH:
            show_error(
                f"Names must be a maximum of {self.MAX_NAME_LENGTH} characters",
                "Name too long",
                False,
            )
            return False
        if name in self.tracker.get_item_names():
            show_error(
                f"Suggested {self.item_name} name is already in use. "
                f"Names in use: {self.tracker.get_item_names()}",
                "Name already in use",
                False,
            )
            return False
        return True

    def generate_repo_name(self) -> str:
        raise NotImplementedError

    def create_repo(self):
        self.name = self.input_name(f"Enter name for {self.reference}")
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

        self.description = self.input_description()

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


def generate_folder_name(document_reference: str, document_name: str) -> str:
    return f"{document_reference}_{re.sub(' ', '', document_name.title())}"
