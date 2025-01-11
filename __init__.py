from .Bowtie_Creator.bowtie_creator_action import BowtiePluginAction
from .Kicadium_DRC.drc_creator_action import DRCPluginAction
from .Project_Creator.project_creator_action import CreatorPluginAction

CreatorPluginAction().register()
BowtiePluginAction().register()
DRCPluginAction().register()
