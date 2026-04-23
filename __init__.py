from .Bowtie_Creator.bowtie_creator_action import BowtiePluginAction
from .Project_Creator.project_creator_action import ProjectCreatorPluginAction
from .Project_Creator.kicad_project_creator_action import (
    KicadProjectCreatorPluginAction,
)

ProjectCreatorPluginAction().register()
KicadProjectCreatorPluginAction().register()
# BowtiePluginAction().register()
