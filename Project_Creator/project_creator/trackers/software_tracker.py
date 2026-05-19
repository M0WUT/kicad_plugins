from pathlib import Path

from project_creator.trackers.repo_tracker import RepoTracker


class SoftwareTracker(RepoTracker):

    @classmethod
    def get_tracker_path(cls) -> Path:
        return Path("software") / "software.csv"

    @classmethod
    def get_item_name(cls) -> str:
        return "software project"

    def update_tracker_readme(self) -> None:
        with open(self.local_tracker_path.parent / "README.md", "w+") as readme:
            readme.write(
                f"# {self.repo_owner} Software project tracker (designed by M0WUT)\n"
            )
            pass  # @TODO
