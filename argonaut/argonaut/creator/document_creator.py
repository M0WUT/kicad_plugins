# Standard imporst
from contextlib import ExitStack
import logging
from pathlib import Path
import re

# Third party imports
from git import InvalidGitRepositoryError

# Local imports
from argonaut.tracker.document_tracker import DocumentTracker
from argonaut.misc.git import (
    GitInfo,
    ensure_git_repo_up_to_date,
    get_git_info,
    git_commit_and_push,
    git_pull,
)
from argonaut.config.supported_document_types import (
    SUPPORTED_DOCUMENT_TYPES,
    get_document_type_from_abbreviation,
)
from argonaut.gui.dialog import (
    abort,
    get_folder_input,
    show_error,
    get_user_choice,
    show_info,
)
from argonaut.creator.project_creator import ProjectCreator, regenerate_project_readme
from argonaut.creator.creator import Creator, generate_folder_name
from argonaut.config.config import PROJECT_JSON_PATH


class DocumentCreator(Creator):
    def run(self):
        local_live_path = self.input_project_folder()
        git_info = self.get_project_git_info(local_live_path)

        self.project_repo_owner = git_info.repo_owner
        self.project_repo_name = git_info.repo_name
        self.project_id = f"P{self.project_repo_name[1:5]}"
        self.logger.debug(f"Working in project {self.project_id}")

        self.tracker = self.context_manager_stack.enter_context(
            DocumentTracker(
                self.project_repo_owner, self.project_repo_name, PROJECT_JSON_PATH
            )
        )
        self.project_root_local_path = self.tracker.local_clone_path

        document_type_str = get_user_choice(
            self.parent_frame,
            [
                f"{self.project_id}-{x.abbreviation}-{self.tracker.generate_next_number(x):03d} ({x.description})"
                for x in SUPPORTED_DOCUMENT_TYPES
            ],
            "Select new document to be created",
        )

        if document_type_str is None:
            abort()

        self.reference = document_type_str.split(" ")[0]
        self.document_type = get_document_type_from_abbreviation(
            self.reference.split("-")[1]
        )
        self.tracker.set_document_type(self.document_type)

        self.logger.info(
            f"New document {self.reference} requested ({self.document_type.description})"
        )
        self.item_name = self.document_type.description
        self.name = self.input_name(f"Enter title for {self.reference}")

        self.description = self.input_description()

        new_document_path = (
            self.project_root_local_path
            / self.document_type.relative_path
            / generate_folder_name(self.reference, self.name)
        )

        self.logger.info(f"Creating new document folder at {new_document_path}")

        tracker_info = self.document_type.template_function(
            new_document_path,
            self.project_repo_owner,
            self.project_repo_name,
            self.document_type,
            self.reference,
            self.name,
            self.description,
        )

        self.tracker.update(self.reference, tracker_info)

        regenerate_project_readme(self.project_root_local_path)

        git_commit_and_push(self.project_root_local_path, f"Added {self.reference}")
        git_pull(local_live_path)

        show_info(f"Successfully created {self.reference}", "Success")

    def input_project_folder(self) -> Path:
        folder = get_folder_input("Select folder inside project repo")
        self.logger.info(f"Selected local path for project: {folder}")
        return folder

    def get_project_git_info(self, local_folder_path: Path) -> GitInfo:

        # Now start at the current folder and work upwards looking for a Git Repo
        # Note that, due to the use of submodules, there may be Git Repos between
        # the selected folder and the project root

        searchable_folders = (
            [local_folder_path] if local_folder_path.is_dir() else []
        ) + list(local_folder_path.parents)

        for folder in searchable_folders:
            self.logger.debug(f"Checking: {folder.absolute()}")
            try:
                git_info = get_git_info(folder)
                self.logger.debug(
                    f"Found repo: {git_info.repo_owner}/{git_info.repo_name} at {folder.absolute()}"
                )

                if not ProjectCreator.is_valid_project_repo_name(git_info.repo_name):
                    self.logger.debug("Doesn't match required name format, ignoring")
                    continue

                self.logger.debug("Repo name matches expected format")
                ensure_git_repo_up_to_date(folder)
                self.logger.info(
                    f"Suitable repo {git_info.repo_owner}/{git_info.repo_name} found at {folder.absolute()}"
                )
                return git_info

            except InvalidGitRepositoryError:
                self.logger.debug("Not a Git repository")
        show_error(
            "Neither the selected directory, nor its parents are a project directory",
            "Not a project directory",
        )
        raise RuntimeError
