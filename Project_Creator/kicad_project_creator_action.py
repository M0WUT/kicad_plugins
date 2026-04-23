from contextlib import suppress
import logging

import pcbnew

from .gh_functions import validate_github_setup
from .logging_handler import configure_logger
from .kicad_project_creator import KicadProjectHandler


class KicadProjectCreatorPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "New Kicad Project Creator"
        self.category = "M0WUT Tools"
        self.description = "Generates new Kicad project repository on Github"

    def Run(self):  # noqa: N802
        # This must be called Run with a capital R to appease Kicad
        with suppress(SystemExit):
            logger = logging.getLogger(__name__)
            configure_logger(logger, logging.DEBUG)
            gh_user = validate_github_setup()
            with KicadProjectHandler(gh_user) as kicad_project_handler:
                kicad_project_handler.create_new_project()
