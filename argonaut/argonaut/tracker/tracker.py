# Standard imports
from dataclasses import dataclass
from pathlib import Path
import json

# Third party imports

# Local imports
from argonaut.gui.dialog import show_error
from argonaut.misc.os import delete_folder, get_temp_dir_path
from argonaut.logger.logger import create_default_logger
from argonaut.misc.git import git_clone


@dataclass
class Tracker:
    project_repo_owner: str
    project_repo_name: str
    relative_json_path: Path

    def __post_init__(self):
        self.logger = create_default_logger(__name__)

    def __enter__(self):
        self.local_clone_path = self.clone_project_repo()
        self.project_json = self.load_project_json()
        return self

    def __exit__(self, *args, **kwargs):
        if self.local_clone_path is not None:
            self.logger.debug(f"Deleting temp file: {self.local_clone_path.absolute()}")
            delete_folder(self.local_clone_path)

    def clone_project_repo(self) -> Path:
        local_clone_path = get_temp_dir_path() / self.project_repo_name
        self.logger.info(
            f"Cloning {self.project_repo_owner}/{self.project_repo_name} to "
            f"{local_clone_path.absolute()}"
        )
        git_clone(self.project_repo_owner, self.project_repo_name, local_clone_path)
        return local_clone_path

    def load_project_json(self) -> dict:
        assert self.local_clone_path is not None
        assert self.relative_json_path is not None
        try:
            self.absolute_json_path = self.local_clone_path / self.relative_json_path
            with open(self.absolute_json_path, "r") as json_file:
                project_json = json.load(json_file)
        except FileNotFoundError:
            show_error(
                f"Project tracking file ({self.project_repo_owner}/"
                f"{self.project_repo_name}/{self.relative_json_path}) not found",
                "File not found",
            )

        self.logger.debug(f"Loaded project information: {project_json}")
        return project_json

    def validate_item_numbers(self, item_numbers: list[int]) -> None:
        highest_item_number = item_numbers[-1]
        if item_numbers != list(range(1, highest_item_number + 1)):
            show_error(
                f"Item numbering is not a continuous list for 1-{highest_item_number}. "
                "Aborting.",
                f"Unexpected {self} numbering",
            )
