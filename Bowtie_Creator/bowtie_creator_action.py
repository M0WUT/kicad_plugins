import pcbnew

from .bowtie_creator import create_bowtie


class BowtiePluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Silly LED Bowtie Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates addressable LED bowtie"

    def Run(self):
        # This must be called Run with a capital R to appease Kicad
        create_bowtie(pcbnew.GetBoard())
