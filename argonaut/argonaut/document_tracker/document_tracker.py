# Standard imports
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

# Third party imports

# Local imports
from argonaut.gui.dialog import ask_question, show_error
from argonaut.config.document_type import DocumentType
from argonaut.misc.git import git_clone
from argonaut.misc.os import delete_folder, get_temp_dir_path
from argonaut.logger.logger import create_default_logger
from argonaut.config.config import PROJECT_JSON_PATH


@dataclass
class DocumentTracker:
    project_repo_owner: str
    project_repo_name: str

    def __post_init__(self):
        self.logger = create_default_logger(__name__)
        self.local_clone_path: Optional[Path] = None

    def __enter__(self):
        self.local_clone_path = self.clone_project_repo()
        self.project_json = self.load_project_json()

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
        try:
            json_path = self.local_clone_path / PROJECT_JSON_PATH
            with open(json_path, "r") as json_file:
                project_json = json.load(json_file)
        except FileNotFoundError:
            show_error(
                f"Project tracking file ({self.project_repo_owner}/{self.project_repo_name}/{PROJECT_JSON_PATH}) not found",
                "File not found",
            )

        self.logger.debug(project_json)
        return project_json

    def generate_next_document_number(self, document_type: DocumentType) -> int:
        pass
