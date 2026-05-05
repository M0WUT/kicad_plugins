from contextlib import suppress

import pcbnew  # pyright: ignore[reportMissingImports]

from .gh_functions import validate_github_setup
from .project_creator import ProjectHandler
from .kicad_project_creator import KicadProjectHandler


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


class KicadProjectCreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "New Kicad Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates new Kicad project repository on Github"

    def Run(self):  # noqa: N802
        # This must be called Run with a capital R to appease Kicad
        with suppress(SystemExit):
            gh_user = validate_github_setup()
            with KicadProjectHandler(gh_user) as kicad_project_handler:
                kicad_project_handler.create_new_project()
