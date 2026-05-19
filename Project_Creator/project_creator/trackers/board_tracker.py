from pathlib import Path

from project_creator.trackers.repo_tracker import RepoTracker


class BoardTracker(RepoTracker):

    @classmethod
    def get_tracker_path(cls) -> Path:
        return Path("hardware") / "boards.csv"

    @classmethod
    def get_item_name(cls) -> str:
        return "board"

    def update_tracker_readme(self) -> None:
        with open(self.local_tracker_path.parent / "README.md", "w+") as readme:
            readme.write(f"# {self.repo_owner} Board tracker (designed by M0WUT)\n")
            readme.write(
                "| Board number | Board name | Description | Full Board ID | Repo URL | Github Pages URL | Github Pages Deployment Status |\n"  # noqa: E501
            )
            readme.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            for (
                number,
                name,
                des,
                board_id,
                repo_url,
                pages_url,
            ) in self.get_item_info():
                readme.write(
                    f"| {number} | {name} | {des} | {board_id} | [Github Repo]({repo_url}) | [Github Pages]({pages_url}) | ![Github Pages deployment]({repo_url}/actions/workflows/{GITHUB_PAGES_DEPLOYMENT_WORKFLOW_NAME}/badge.svg) |\n"  # noqa: E501
                )
