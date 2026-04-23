from contextlib import suppress


from .project_creator import create_project
import pcbnew


class CreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "New Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates new project master repository on Github"

    def Run(self):  # noqa: N802
        # This must be called Run with a capital R to appease Kicad
        with suppress(SystemExit):
            create_project()
