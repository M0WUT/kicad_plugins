from .github_helper import (
    check_if_github_cli_exists,
    get_current_github_user,
    check_if_project_exists,
    create_blank_github_repo,
)
from .ui import show_error, get_text_input, show_warning, show_info, get_folder_input
import logging
from .logging_handler import configure_logger
import re


class ProjectCreator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging.DEBUG)

    def run(self):
        # Check if Github CLI is present
        if check_if_github_cli_exists() is False:
            show_error(
                "Github CLI not found. Please ensure it is installed and authenticated",
                "Github CLI not found",
            )

        # Query for Github user
        valid_project_name = False
        gh_user = get_current_github_user()

        # Get an new project name
        self.logger.info(f"Github user detected as {gh_user}")

        while not valid_project_name:
            requested_project_name = get_text_input(
                message="Please enter requested repo name", title="Enter repo name"
            )

            requested_repo_name = re.sub(" ", "-", requested_project_name.lower())
            if check_if_project_exists(gh_user, requested_repo_name) is False:
                # New project name
                valid_project_name = True
                project_name = requested_project_name
                repo_name = requested_repo_name
                self.logger.info(
                    f'Creating project "{project_name}" at github.com/{gh_user}/{repo_name}'
                )
            else:
                show_warning(f"Repo {gh_user}/{requested_repo_name} already exists")

        # Create blank repo
        show_info(
            f"This will create a default Kicad project in the {gh_user}/{repo_name} repository. Press OK to continue...",
            title="Here we go!",
        )

        # create_blank_github_repo(repo_name)
        # self.logger.info(f"{gh_user}/{repo_name} created")

        # Select parent folder for checkout
        repo_parent_folder = get_folder_input("Please select parent directory for checkout", "Select parent folder")



def run():
    x = ProjectCreator()
    x.run()


if __name__ == "__main__":
    run()
