import pcbnew

from . import project_creator


class CreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Kicad Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates New project with M0WUT settings applied"

    def Run(self):
        project_creator.run()