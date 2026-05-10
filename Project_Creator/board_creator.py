# Standard imports
import json
import logging
from pathlib import Path
import re

# Third party imports
from git import InvalidGitRepositoryError

# Local imports
from .repo_secrets import REPO_SECRETS
from .creator import Creator
from .repo_tracker import BoardTracker, ProjectTracker
from .git_functions import (
    add_github_secret,
    copy_files_from_git_repo,
    ensure_git_repo_up_to_date,
    get_git_info,
    git_add_submodule,
    git_commit_and_push,
    git_clone,
    git_pull_including_submodules,
    set_github_pages_source_to_actions,
)
from .os_functions import delete_folder, get_temp_dir_path
from .ui import (
    ask_question,
    get_folder_input,
    show_error,
    show_info,
    show_warning,
)
from .config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    RELEASER_PROJECT_REPO_NAME,
    RELEASER_PROJECT_REPO_OWNER,
    TEMPLATE_PROJECT_REPO_NAME,
    TEMPLATE_PROJECT_REPO_OWNER,
)
from .logging_handler import configure_logger


class BoardCreator(Creator):

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)
        self.hardware_folder_path = self.select_local_hardware_folder()
        self.project_path = self.hardware_folder_path.parent
        self.project_git_info = get_git_info(self.project_path)

        self.logger.info(f'Detected repo "{self.project_git_info.upstream}"')
        self.board_repo_owner = self.project_git_info.github_repo_owner
        self.board_repo_name = self.project_git_info.github_repo_name

        # First 5 characters of repo name should be pxxxx
        # where xxxx is zero-padded project number
        try:
            self.project_number = int(self.project_git_info.github_repo_name[1:5])
        except ValueError:
            show_error(
                f'Detected repo "{self.project_git_info.upstream}" does not appear '
                "to be managed by M0WUT kicad plugins",
                "Unsupported repo",
            )
        self.logger.info(f"Detected project P{self.project_number:04d}")

        super().__init__(
            self.board_repo_owner, self.board_repo_name, "board", self.logger
        )
        # The tracker for boards should be in the project repo
        self._tracker = BoardTracker(self.board_repo_owner, self.board_repo_name)

    def select_local_hardware_folder(self) -> Path:
        local_folder_path = get_folder_input(
            "Select parent folder for new Kicad project"
        )
        self.logger.info(f"Selected local path for project: {local_folder_path}")

        # Three options here:
        #   1) In the "hardware" subfolder of a project top-level repo
        #   2) In a project top-level repo
        #   3) Not in a child of a project repo (may or may not be in a Git repo)

        try:
            ensure_git_repo_up_to_date(local_folder_path)
            git_info = get_git_info(local_folder_path)
            self.logger.info(git_info)

            # Option 2
            possible_hardware_folder_path = local_folder_path / "hardware"
            if (
                possible_hardware_folder_path.exists()
                and possible_hardware_folder_path.is_dir()
            ):
                # Hardware folder is already created
                self.logger.info(
                    f'Found hardware folder at "{possible_hardware_folder_path}"'
                )
                return possible_hardware_folder_path
            else:
                # Project repository does not yet have hardware folder
                if ask_question(
                    "OK to create hardware folder for repo "
                    f'"{git_info.github_repo_owner}/{git_info.github_repo_name}"?',
                    "Create hardware folder?",
                ):
                    possible_hardware_folder_path.mkdir(mode=660)
                    return possible_hardware_folder_path
                else:
                    show_error("User Aborted", "User aborted")

        except InvalidGitRepositoryError:
            if local_folder_path.stem == "hardware":
                try:
                    # Option 1
                    ensure_git_repo_up_to_date(local_folder_path.parent)
                    git_info = get_git_info(local_folder_path.parent)
                    self.logger.info(git_info)
                    # Option 1 - already there
                    self.logger.info(f'Using hardware folder at "{local_folder_path}"')
                    return local_folder_path
                except InvalidGitRepositoryError:
                    pass

            # Option 3
            self.logger.info(
                "Selected folder is not in a Git repo or its subdirectories"
            )

            # Could possibly do something nicer e.g. allow user to select which repo
            # they want to base this on but not bothering for now
            show_warning(
                "Selected folder is not a Git repository",
                "Not a Git Repo",
            )
            raise NotImplementedError

    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return (
            f"p{self.project_number:04d}-{self.number:03d}_{github_sanitised_repo_name}"
        )

    @classmethod
    def format_item_number(cls, number: int):
        return f"{number:03d}"

    def create_new_board(self):
        self.create_new_repo()

        self.board_number = self.number
        self.board_name = self.name
        self.board_description = self.description

        self.board_id = f"P{self.project_number:04d}-{self.board_number:03d}"

        temp_path = get_temp_dir_path() / "foo"
        git_clone(self.board_repo_owner, self.board_repo_name, temp_path)
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

        self.local_folder = self._tracker.local_clone_path / kicad_project_relative_path

        git_add_submodule(
            self._tracker.local_clone_path,
            kicad_project_relative_path,
            f"https://github.com/{self.board_repo_owner}/{self.board_repo_name}.git",
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
        new_file_stem = f"{self.board_repo_name}"
        for file in self.local_folder.rglob(f"{str_to_replace}*"):
            file.rename(file.parent / f"{new_file_stem}{file.suffix}")

        # Replace text content in files
        for path in self.local_folder.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                try:
                    text = path.read_text(encoding="utf-8")
                    path.write_text(
                        text.replace(str_to_replace, new_file_stem),
                        encoding="utf-8",
                    )
                except UnicodeDecodeError:
                    print(f"Not a text file: {path}")

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
                self.board_repo_owner, self.board_repo_name, secret_name, secret_value
            )

        # Enable workflow as Github pages source
        set_github_pages_source_to_actions(self.board_repo_owner, self.board_repo_name)

        # Replace project text strings
        kicad_project_file_paths = list(self.local_folder.rglob("*.kicad_pro"))
        assert len(kicad_project_file_paths) == 1, "Multiple kicad project files found"
        with open(kicad_project_file_paths[0]) as project_file:
            project_json = json.load(project_file)

        with ProjectTracker(
            self.board_repo_owner, PROJECT_NUMBER_TRACKER_REPO_NAME
        ) as _project_tracker:

            project_text_variables = {
                "WUT_BOARD_NAME": self.board_name,
                "WUT_BOARD_NUMBER": f"{self.board_number:03d}",
                "WUT_COMPANY": self.board_repo_owner,
                "WUT_GITHUB_PAGES_URL": f"{self.board_repo_owner.lower()}.github.com/{self.board_repo_name}",  # noqa: E501
                "WUT_GITHUB_URL": f"https://github.com/{self.board_repo_owner}/{self.board_repo_name}",  # noqa: E501
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

        self._tracker.update_tracker_repo(
            self.board_number,
            self.board_name,
            [
                self.board_description,
                self.board_id,
                f"https://github.com/{self.board_repo_owner}/{self.board_repo_name}",
                f"https://{self.board_repo_owner}.github.io/{self.board_repo_name}",
            ],
        )

        # Finally git pull on the local folder
        git_pull_including_submodules(self.project_path)

        show_info(
            f"Successfully created board: {self.board_id}\n"
            f"Board number: P{self.project_number:04d}\n"
            f"Board name: {self.board_name}\n"
            f"Description: {self.board_description}\n"
            f"Github repo: {self.board_repo_owner}/{self.board_repo_name}\n",
            "Board creation complete",
        )


if __name__ == "__main__":
    import wx

    _ = wx.App()
    with BoardCreator() as x:
        x.create_new_board()
