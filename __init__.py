from .Bowtie_Creator.bowtie_creator_action import BowtiePluginAction
from .Project_Creator.project_creator_actions import (
    ProjectCreatorPluginAction,
    KicadProjectCreatorPluginAction,
)


ProjectCreatorPluginAction().register()
KicadProjectCreatorPluginAction().register()
# BowtiePluginAction().register()
