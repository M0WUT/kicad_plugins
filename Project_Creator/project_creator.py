import logging

from .logging_handler import configure_logger
from .github_helper import validate_github_setup
from .project_funcs import ProjectHandler


def create_project():
    logger = logging.getLogger(__name__)
    configure_logger(logger, logging.DEBUG)
    gh_user = validate_github_setup()
    with ProjectHandler(gh_user) as project_handler:
        project_handler.create_new_project()
