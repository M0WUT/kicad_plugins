# Standard imporst
from contextlib import ExitStack
import logging
from pathlib import Path

# Third party imports
from git import InvalidGitRepositoryError

# Local imports
from argonaut.tracker.document_tracker import DocumentTracker
from argonaut.misc.git import GitInfo, ensure_git_repo_up_to_date, get_git_info
from argonaut.config.document_type import SUPPORTED_DOCUMENT_TYPES
from argonaut.gui.dialog import get_folder_input, show_error, get_user_choice
from argonaut.creator.project_creator import ProjectCreator
from argonaut.creator.creator import Creator


class DocumentCreator(Creator):
    def run(self):
        project_subfolder = self.input_project_folder()
        git_info = self.get_project_git_info(project_subfolder)

        self.project_root_local_path = git_info.local_path
        self.project_repo_owner = git_info.repo_owner
        self.project_repo_name = git_info.repo_name
        self.project_id = f"P{self.project_repo_name[1:5]}"
        self.logger.debug(f"Working in project {self.project_id}")

        self.document_tracker = self.context_manager_stack.enter_context(
            DocumentTracker(self.project_repo_owner, self.project_repo_name)
        )

        self.document_type_str = get_user_choice(
            self.parent_frame,
            [f"{x.abbreviation} - {x.description}" for x in SUPPORTED_DOCUMENT_TYPES],
            "Select new document type",
        )

        self.logger.debug(f"User requested {self.document_type_str}")

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
