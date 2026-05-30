# Standard imports
from contextlib import suppress
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re

# Third party imports
from git import InvalidGitRepositoryError

# Local imports
from project_creator.repo_secrets import REPO_SECRETS
from project_creator.creators.repo_creator import RepoCreator
from project_creator.trackers import BoardTracker, ProjectTracker, RepoTracker

from argonaut.argonaut.misc.git import (
    add_github_secret,
    copy_files_from_git_repo,
    ensure_git_repo_up_to_date,
    get_git_info,
    get_repo_owner_name_from_url,
    git_add_submodule,
    git_checkout,
    git_commit_and_push,
    git_clone,
    git_pull_including_submodules,
    set_github_pages_source_to_actions,
)
from argonaut.argonaut.misc.os import delete_folder, get_temp_dir_path
from argonaut.argonaut.gui.ui import (
    abort,
    ask_question,
    get_folder_input,
    show_error,
    show_info,
    show_warning,
)
from config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    RELEASER_PROJECT_REPO_NAME,
    RELEASER_PROJECT_REPO_OWNER,
    TEMPLATE_PROJECT_REPO_NAME,
    TEMPLATE_PROJECT_REPO_OWNER,
)
from argonaut.argonaut.logger.logger import configure_logger


class SubprojectCreator(RepoCreator):
    """
    Repo Creator for any repo that lives within a parent
    project.
    """

    def generate_repo_name(self) -> str:
        raise NotImplementedError

    @classmethod
    def format_item_number(cls, number: int):
        raise NotImplementedError

    def get_tracker_class(self) -> type[RepoTracker]:
        raise NotImplementedError

    def create_tracker(self):
        self._tracker_class = self.get_tracker_class()
        project_repo_owner, project_repo_name = self._get_project_info_from_path()
        return self._tracker_class(project_repo_owner, project_repo_name)

    def _get_project_info_from_path(self) -> tuple[str, str]:

        with ProjectTracker(
            self.repo_owner, PROJECT_NUMBER_TRACKER_REPO_NAME
        ) as project_tracker:
            project_details = [
                get_repo_owner_name_from_url(x[3])
                for x in project_tracker.get_item_info()
            ]

        # Select any folder that is either the Git clone folder
        # or one of its children. This will recurse upwards
        local_folder_path = get_folder_input(
            f"Select parent folder for new {self._tracker_class.get_item_name()} repo"
        )
        self.logger.info(f"Selected local path for project: {local_folder_path}")

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
                self.logger.debug(git_info)
                repo_details = (git_info.repo_owner, git_info.repo_name)
                if repo_details in project_details:
                    if ask_question(
                        f'Found a checkout of "{git_info.repo_owner}/'
                        f'{git_info.repo_name}" in "{folder.absolute()}". '
                        "Is this correct?",
                        "Confirm repo",
                    ):
                        ensure_git_repo_up_to_date(folder)
                        self.project_path = folder
                        return repo_details
                    else:
                        abort()
            except InvalidGitRepositoryError:
                self.logger.debug("Not a Git repository")
        show_error(
            "Neither the selected directory, nor its parents are a project directory",
            "Not a project directory",
        )
        raise RuntimeError
