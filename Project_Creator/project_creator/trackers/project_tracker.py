from pathlib import Path

from project_creator.trackers.repo_tracker import RepoTracker


class ProjectTracker(RepoTracker):

    @classmethod
    def get_tracker_path(cls) -> Path:
        return Path("projects.csv")

    @classmethod
    def get_item_name(cls) -> str:
        return "project"

    def update_tracker_readme(self) -> None:
        with open(self.local_tracker_path.parent / "README.md", "w+") as readme:
            readme.write(f"# {self.repo_owner} Project tracker (designed by M0WUT)\n")
            readme.write("| Project number | Project name | Description | URL |\n")
            readme.write("| --- | --- | --- | --- |\n")
            for number, name, des, url in self.get_item_info():
                readme.write(f"| {number} | {name} | {des} | [Main Repo]({url})\n")
