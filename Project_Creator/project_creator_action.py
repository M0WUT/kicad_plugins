from contextlib import suppress

import pcbnew

from .project_creator import ProjectCreator


class CreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Kicad Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates New project with M0WUT settings applied"

    def Run(self):
        # This must be called Run with a capital R to appease Kicad
        with suppress(SystemExit):
            _ = ProjectCreator()
