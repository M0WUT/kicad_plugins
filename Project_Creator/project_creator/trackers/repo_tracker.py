# Standard imports
import csv
from pathlib import Path
import logging
import re
from dataclasses import dataclass

# Third party imports

# Local imports
from config import GITHUB_PAGES_DEPLOYMENT_WORKFLOW_NAME
from project_creator.logging_handler import configure_logger
from project_creator.ui import abort, ask_question, show_error
from project_creator.os_functions import delete_folder, get_temp_dir_path
from project_creator.git_functions import (
    git_clone,
    git_commit_and_push,
)

"""
Philosophy is that there is a repo on Github that contains a csv file reponsible
for tracking child repos. Examples of this maybe:
1) Project tracker repo keeping track of all projects
2) Boards tracker within a project repo keeps track of all board repos in that project
    (same for software / firmware / docs etc)

Within the folder containing the csv, there is also expected to be a README that should
be updated to visualise the contents of the csv tracker. The csv is the source of truth
"""


@dataclass
class RepoTracker:
    repo_owner: str
    repo_name: str

    MAX_NAME_LENGTH = 32

    NUMBER_FIELD_INDEX = 0
    NAME_FIELD_INDEX = 1

    def __post_init__(self):
        self.logger: logging.Logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)
        self.clone_repo()
        self.tracker_path = self.get_tracker_path()
        self.ensure_tracker_file_exists()
        self.item_name = self.get_item_name()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        delete_folder(self.local_clone_path)

    @classmethod
    def get_tracker_path(cls) -> Path:
        raise NotImplementedError

    @classmethod
    def get_item_name(cls) -> str:
        raise NotImplementedError

    def update_tracker_readme(self) -> None:
        raise NotImplementedError

    def clone_repo(self) -> None:
        local_clone_path = get_temp_dir_path() / self.repo_name
        self.logger.info(
            f'Cloning "{self.repo_owner}/{self.repo_name}" to '
            f'"{local_clone_path.absolute()}"'
        )
        git_clone(self.repo_owner, self.repo_name, local_clone_path)
        self.local_clone_path: Path = local_clone_path

    def ensure_tracker_file_exists(self) -> None:
        local_tracker_path = self.local_clone_path / self.tracker_path
        if not local_tracker_path.exists():
            if ask_question(
                f"OK to create {self.tracker_path.parent.stem} folder in repo "
                f'"{self.repo_owner}/{self.repo_name}"',
                f"OK to create {self.item_name} tracker?",
            ):
                local_tracker_path.parent.mkdir(parents=True, exist_ok=True)
                local_tracker_path.touch()
            else:
                abort()
        self.local_tracker_path: Path = local_tracker_path

    def get_item_info(self) -> list[list[str]]:
        with open(self.local_tracker_path, "r") as file:
            reader = csv.reader(file, quotechar='"', delimiter=",")
            existing_items = [x for x in reader]
        self.logger.info(f"Loaded info of {len(existing_items)} {self.item_name}s")
        return existing_items

    def generate_next_item_number(self) -> int:
        """
        Tracker is expected to contain a unique serial number
        in the first column. This will return the serial number
        for an item that is about to be created
        """
        existing_item_numbers = [
            int(x[self.NUMBER_FIELD_INDEX]) for x in self.get_item_info()
        ]
        if existing_item_numbers == []:
            next_item_number = 1  # One indexing
        else:

            self.validate_item_numbers(existing_item_numbers)
            next_item_number = existing_item_numbers[-1] + 1

        self.logger.info(f"Next available number is {next_item_number}")

        return next_item_number

    def validate_item_numbers(self, item_numbers: list[int]) -> None:
        highest_item_number = item_numbers[-1]
        if item_numbers != [x for x in range(1, highest_item_number + 1)]:
            show_error(
                f"Item numbering is not a continuous list for 1-{highest_item_number}. "
                "Aborting.",
                f"Unexpected {self.item_name} numbering",
            )

    def get_item_names(self) -> list[str]:
        return [x[self.NAME_FIELD_INDEX] for x in self.get_item_info()]

    def validate_str(self, x: str) -> bool:
        return bool(re.fullmatch(r"(?=.*[A-Za-z0-9])[A-Za-z0-9 ]+", x))

    def validate_item_name(self, name: str) -> bool:
        if not self.validate_str(name):
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
        if name in self.get_item_names():
            show_error(
                f"Suggested {self.item_name} name is already in use. "
                f"Names in use: {self.get_item_names()}",
                "Name already in use",
                False,
            )
            return False
        return True

    def update_tracker_file(
        self, new_item_number: int, new_item_name: str, other_fields: list[str]
    ) -> None:
        assert new_item_number == self.generate_next_item_number()
        assert self.validate_item_name(new_item_name)
        with open(self.local_tracker_path, "a") as file:
            file.write(
                ",".join(
                    [str(new_item_number), str(new_item_name)]
                    + [str(x) for x in other_fields]
                )
            )
            file.write("\n")

    def update_tracker_repo(
        self, new_item_number: int, new_item_name: str, other_fields: list[str]
    ) -> None:
        self.update_tracker_file(new_item_number, new_item_name, other_fields)
        self.update_tracker_readme()
        git_commit_and_push(
            self.local_clone_path, f"Added {self.item_name} number {new_item_number}"
        )
        self.logger.info("Successfully updated tracker")

    def get_item_name_from_number(self, item_number: int):
        possible_names = [
            x[self.NAME_FIELD_INDEX]
            for x in self.get_item_info()
            if int(x[self.NUMBER_FIELD_INDEX]) == item_number
        ]

        if len(possible_names) != 1:
            raise ValueError(
                f"Could not find item with number {item_number} "
                f"in {self.get_item_info()}"
            )
        return possible_names[0]
