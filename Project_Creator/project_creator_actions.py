# Standard imports
from contextlib import suppress
from pathlib import Path

# Third party imports
import pcbnew  # pyright: ignore[reportMissingImports]

# Local imports
from .os_functions import delete_folder
from .git_functions import copy_files_from_git_repo, validate_github_setup
from .project_creator import ProjectCreator
from .board_creator import BoardCreator
from .config import (
    PROJECT_NUMBER_TRACKER_REPO_NAME,
    RELEASER_PROJECT_REPO_NAME,
    RELEASER_PROJECT_REPO_OWNER,
    TEMPLATE_PROJECT_REPO_NAME,
    TEMPLATE_PROJECT_REPO_OWNER,
)
from .ui import get_folder_input, show_error, show_info


class ProjectCreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "New Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates new project super repository on Github"

    def Run(self):  # noqa: N802
        # This must be called Run with a capital R to appease Kicad
        with suppress(SystemExit):
            gh_user = validate_github_setup()
            with ProjectCreator(
                gh_user, PROJECT_NUMBER_TRACKER_REPO_NAME
            ) as project_creator:
                project_creator.create_new_project()


class KicadBoardCreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "New Kicad Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates new Kicad project repository on Github"

    def Run(self):  # noqa: N802
        with suppress(SystemExit):
            validate_github_setup()
            with BoardCreator() as kicad_project_handler:
                kicad_project_handler.create_new_board()


class UpdateKicadTemplatesPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Update Kicad project templates"
        self.category = "M0WUT Tools"
        self.description = "Updates templates files in existing Kicad board project"

    def Run(self):  # noqa: N802
        with suppress(SystemExit):
            validate_github_setup()
            project_folder = Path(pcbnew.GetBoard().GetFileName()).parent

            templates_folder = project_folder / "Templates"
            github_folder = project_folder / ".github"

            for folder in [templates_folder, github_folder]:
                if not folder.exists() and folder.is_dir():
                    show_error(
                        f'Folder structure of "{project_folder.absolute()}" does '
                        f'not match expectations. Cannot find "{folder.absolute()}"',
                        "Unexpected folder structure",
                    )
                delete_folder(folder)

            copy_files_from_git_repo(
                TEMPLATE_PROJECT_REPO_OWNER,
                TEMPLATE_PROJECT_REPO_NAME,
                project_folder,
                include_paths=[Path("Templates")],
            )

            # Copy Github actions folder
            copy_files_from_git_repo(
                RELEASER_PROJECT_REPO_OWNER,
                RELEASER_PROJECT_REPO_NAME,
                project_folder,
                include_paths=[Path("github")],
            )
            (project_folder / "github").rename(project_folder / ".github")

            show_info("Templates updated", "Templates updated")
