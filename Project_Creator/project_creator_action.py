from contextlib import suppress
import logging

import pcbnew

from .gh_functions import validate_github_setup
from .logging_handler import configure_logger
from .project_creator import ProjectHandler


class ProjectCreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "New Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates new project super repository on Github"

    def Run(self):  # noqa: N802
        # This must be called Run with a capital R to appease Kicad
        with suppress(SystemExit):
            gh_user = validate_github_setup()
            with ProjectHandler(gh_user) as project_handler:
                project_handler.create_new_project()
