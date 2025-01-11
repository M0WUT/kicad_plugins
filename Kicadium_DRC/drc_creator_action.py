import pcbnew

# from .bowtie_creator import create_bowtie


class DRCPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "DRC Generator"
        self.category = "M0WUT Tools"
        self.description = "Generates DRC files with an Altium-esque interface"

    def Run(self):
        # This must be called Run with a capital R to appease Kicad
        print("Hello world")
