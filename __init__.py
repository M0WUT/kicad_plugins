# from .Bowtie_Creator.bowtie_creator_action import BowtiePluginAction
from .Project_Creator.project_creator_actions import (
    ProjectCreatorPluginAction,
    KicadBoardCreatorPluginAction,
)

ProjectCreatorPluginAction().register()
KicadBoardCreatorPluginAction().register()
# BowtiePluginAction().register()
