# Standard imports
import json

# Third party imports

# Local imports
from argonaut.misc.git import git_commit_and_push
from argonaut.tracker.tracker import Tracker
from argonaut.config.config import (
    PROJECT_TRACKER_REPO_NAME,
    PROJECT_TRACKER_REPO_OWNER,
    PROJECT_TRACKER_JSON_PATH,
)


class ProjectTracker(Tracker):
    def generate_next_project_number(self) -> int:
        assert (
            self.project_json is not None
        ), "Project JSON must be loaded before searching"

        if self.project_json == {}:
            return 1

        current_project_numbers = [int(x[1:5]) for x in self.project_json.keys()]

        # Validate item numbers will ensure that the existing numbers
        # are a continuous list from 1-N and are sorted numerically
        self.validate_item_numbers(current_project_numbers)

        return current_project_numbers[-1] + 1

    def get_item_names(self) -> list[str]:
        return [x["name"] for x in self.project_json.values()]

    def update(self, project_reference: str, name: str, description: str, url: str):
        self.project_json[project_reference] = {
            "name": name,
            "description": description,
            "url": url,
            "documents": {},
        }
        with open(self.absolute_json_path, "w") as file:
            json.dump(self.project_json, file)

        self.regenerate_readme()

        git_commit_and_push(self.local_clone_path, f"Added {project_reference}")

    def regenerate_readme(self):
        with open(self.local_clone_path / "README.md", "w+") as readme:
            readme.write("# M0WUT project tracker\n")
            readme.write("| Project reference | Project name | Description | URL |\n")
            readme.write("| --- | --- | --- | --- |\n")
            for ref, items in self.project_json.items():
                readme.write(
                    f"| {ref} | {items['name']} | {items['description']} | [Main Repo]({items['url']})\n"
                )
