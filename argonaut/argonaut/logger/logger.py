# Standard imports
import logging

# Third party imports

# Local imports
from argonaut.config.config import DEFAULT_LOGGING_DEBUG_LEVEL


def create_default_logger(
    name: str, logging_level: int = DEFAULT_LOGGING_DEBUG_LEVEL
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging_level)

    # remove default handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # create console handler
    console_handle = logging.StreamHandler()
    console_handle.setLevel(logging_level)

    # create formatter
    formatter = logging.Formatter("%(name)-10s - %(levelname)-8s - %(message)s")
    console_handle.setFormatter(formatter)

    logger.addHandler(console_handle)

    return logger
