import logging


def configure_logger(logger: logging.Logger, logging_level: int) -> None:
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
