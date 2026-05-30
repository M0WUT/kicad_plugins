import re

from argonaut.argonaut.misc.git import (
    generate_github_repo_url,
    git_add_submodule,
    git_checkout,
    git_clone,
    git_commit_and_push,
    git_pull_including_submodules,
)
from argonaut.argonaut.misc.os import delete_folder, get_temp_dir_path
from argonaut.argonaut.gui.ui import show_info
from project_creator.creators.repo_creator import RepoCreator
from project_creator.trackers.software_tracker import SoftwareTracker
from project_creator.trackers.repo_tracker import RepoTracker


class SoftwareCreator(RepoCreator):
    def generate_repo_name(self) -> str:
        github_sanitised_repo_name = re.sub(" ", "-", self.name.lower())
        return f"{self.id.lower()}_" f"{github_sanitised_repo_name}"

    @classmethod
    def format_item_number(cls, number: int):
        return f"{number:03d}"

    def get_tracker_class(self) -> type[RepoTracker]:
        return SoftwareTracker

    def create_new_software_project(self):
        self.create_new_repo()
        self.id = (
            f"P{self.project_number:04d}-SW-{self.format_item_number(self.number)}"
        )

        temp_path = get_temp_dir_path() / "foo"
        git_clone(self.repo_owner, self.repo_name, temp_path)
        readme_path = temp_path / "README.md"
        with open(readme_path, "w+") as readme_file:
            readme_file.write(f"# {self.id} - {self.name}\n")
            readme_file.write(f"{self.description}\n")
        git_commit_and_push(temp_path, "added README")
        delete_folder(temp_path)

        project_relative_path = (
            self.tracker.get_tracker_path().parent
            / f"{self.id}_{self.name.title().replace(' ', '')}"
        )

        assert self.tracker is not None
        self.local_folder = self.tracker.local_clone_path / project_relative_path

        git_add_submodule(
            self.tracker.local_clone_path,
            project_relative_path,
            generate_github_repo_url(self.repo_owner, self.repo_name),
        )

        self.tracker.update_tracker_repo(
            self.number,
            self.name,
            [
                self.description,
                self.id,
                f"https://github.com/{self.repo_owner}/{self.repo_name}",
                f"https://{self.repo_owner}.github.io/{self.repo_name}",
            ],
        )

        # Finally git pull on the local folder
        git_pull_including_submodules(self.project_path)
        git_checkout(self.project_path / project_relative_path, "main")

        show_info(
            f"Successfully created subproject: {self.id}\n"
            f"Board number: P{self.project_number:04d}\n"
            f"Name: {self.name}\n"
            f"Description: {self.description}\n"
            f"Github repo: {self.repo_owner}/{self.repo_name}\n",
            "Subproject creation complete",
        )


if __name__ == "__main__":
    import wx

    _ = wx.App()
    with SoftwareCreator("M0WUT") as x:
        x.create_new_software_project()
