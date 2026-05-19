# Standard imports
from contextlib import suppress
import json
import logging
from pathlib import Path
import re

# Third party imports
from git import InvalidGitRepositoryError

# Local imports
from project_creator.trackers.repo_tracker import RepoTracker
from project_creator.creators import SubprojectCreator
from project_creator.repo_secrets import REPO_SECRETS
from Project_Creator.creator.creator import RepoCreator
from project_creator.trackers.repo_tracker import BoardTracker, ProjectTracker
from project_creator.git_functions import (
    add_github_secret,
    copy_files_from_git_repo,
    ensure_git_repo_up_to_date,
    get_git_info,
    git_add_submodule,
    git_checkout,
    git_commit_and_push,
    git_clone,
    git_pull_including_submodules,
    set_github_pages_source_to_actions,
    generate_github_pages_url,
    generate_github_repo_url,
)
from project_creator.os_functions import delete_folder, get_temp_dir_path
from project_creator.ui import (
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


class BoardCreator(SubprojectCreator):

    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return f"p{self.project_number:04d}-PCB-{self.number:03d}_{github_sanitised_repo_name}"

    @classmethod
    def format_item_number(cls, number: int):
        return f"{number:03d}"

    def get_tracker_class(self) -> type[RepoTracker]:
        return BoardTracker

    def create_new_board(self):
        self.create_new_repo()
        self.board_number = self.number
        self.board_name = self.name
        self.board_description = self.description

        self.board_id = f"P{self.project_number:04d}-{self.board_number:03d}"

        temp_path = get_temp_dir_path() / "foo"
        git_clone(self.repo_owner, self.repo_name, temp_path)
        readme_path = temp_path / "README.md"
        with open(readme_path, "w+") as readme_file:
            readme_file.write(f"# {self.board_id} - {self.board_name}\n")
            readme_file.write(f"{self.board_description}\n")
        git_commit_and_push(temp_path, "added README")
        delete_folder(temp_path)

        kicad_project_relative_path = (
            Path("hardware")
            / f"{self.board_id}_{self.board_name.title().replace(' ', '')}"
        )

        assert self.tracker is not None
        self.local_folder = self.tracker.local_clone_path / kicad_project_relative_path

        git_add_submodule(
            self.tracker.local_clone_path,
            kicad_project_relative_path,
            f"https://github.com/{self.repo_owner}/{self.repo_name}.git",
        )

        # Get template project files
        copy_files_from_git_repo(
            TEMPLATE_PROJECT_REPO_OWNER,
            TEMPLATE_PROJECT_REPO_NAME,
            self.local_folder,
            exclude_paths=[Path("README.md")],
        )

        # Rename files
        str_to_replace = TEMPLATE_PROJECT_REPO_NAME
        new_file_stem = f"{self.repo_name}"
        for file in self.local_folder.rglob(f"{str_to_replace}*"):
            file.rename(file.parent / f"{new_file_stem}{file.suffix}")

        # Replace text content in files
        for path in self.local_folder.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                with suppress(UnicodeDecodeError):
                    text = path.read_text(encoding="utf-8")
                    path.write_text(
                        text.replace(str_to_replace, new_file_stem),
                        encoding="utf-8",
                    )

        # Copy Github actions folder
        copy_files_from_git_repo(
            RELEASER_PROJECT_REPO_OWNER,
            RELEASER_PROJECT_REPO_NAME,
            self.local_folder,
            include_paths=[Path("github")],
        )
        (self.local_folder / "github").rename(self.local_folder / ".github")

        # Copy secrets over
        for secret_name, secret_value in REPO_SECRETS.items():
            add_github_secret(
                self.repo_owner, self.repo_name, secret_name, secret_value
            )

        # Enable workflow as Github pages source
        set_github_pages_source_to_actions(self.repo_owner, self.repo_name)

        # Replace project text strings
        kicad_project_file_paths = list(self.local_folder.rglob("*.kicad_pro"))
        assert len(kicad_project_file_paths) == 1, "Multiple kicad project files found"
        with open(kicad_project_file_paths[0]) as project_file:
            project_json = json.load(project_file)

        with ProjectTracker(
            self.repo_owner, PROJECT_NUMBER_TRACKER_REPO_NAME
        ) as _project_tracker:

            project_text_variables = {
                "WUT_BOARD_NAME": self.board_name,
                "WUT_BOARD_NUMBER": f"{self.board_number:03d}",
                "WUT_COMPANY": self.repo_owner,
                "WUT_GITHUB_PAGES_URL": generate_github_pages_url(
                    self.repo_owner, self.repo_name
                ),  # noqa: E501
                "WUT_GITHUB_URL": generate_github_repo_url(
                    self.repo_owner, self.repo_name
                ),  # noqa: E501
                "WUT_GIT_COMMIT_DATE": "",
                "WUT_GIT_COMMIT_TIME": "",
                "WUT_GIT_COMMIT_TAG": "",
                "WUT_GIT_VERSION": "",
                "WUT_LAYOUT_VERSION": "1",
                "WUT_PROJECT_NAME": _project_tracker.get_item_name_from_number(
                    self.project_number
                ),
                "WUT_PROJECT_NUMBER": f"{self.project_number:04d}",
                "WUT_RELEASE_STATUS": "DRAFT",
                "WUT_SCHEMATIC_VERSION": "1",
            }

        project_json["text_variables"] = project_text_variables

        with open(kicad_project_file_paths[0], "w") as project_file:
            json.dump(project_json, project_file, indent=2)

        git_commit_and_push(self.local_folder, "Added template files")

        self.tracker.update_tracker_repo(
            self.board_number,
            self.board_name,
            [
                self.board_description,
                self.board_id,
                f"https://github.com/{self.repo_owner}/{self.repo_name}",
                f"https://{self.repo_owner}.github.io/{self.repo_name}",
            ],
        )

        # Finally git pull on the local folder
        git_pull_including_submodules(self.project_path)
        git_checkout(self.project_path / kicad_project_relative_path, "main")

        show_info(
            f"Successfully created board: {self.board_id}\n"
            f"Board number: P{self.project_number:04d}\n"
            f"Board name: {self.board_name}\n"
            f"Description: {self.board_description}\n"
            f"Github repo: {self.repo_owner}/{self.repo_name}\n",
            "Board creation complete",
        )


if __name__ == "__main__":
    import wx

    _ = wx.App()
    with BoardCreator("M0WUT") as x:
        x.create_new_board()
