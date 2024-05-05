import logging
from pathlib import Path

from logging_handler import configure_logger

from ..utils.platform import get_kicad_path


class KicadProjectCreator:
    def __init__(self, logging_level=logging.WARNING):

        self.logger: logging.Logger
        self.kicad_path: Path
        self.kicad_cli_path: Path

        self.logger = logging.getLogger(__name__)
        configure_logger(self.logger, logging_level)

        kicad_directory = get_kicad_path()
        self.kicad_path = kicad_directory / "kicad"
        self.kicad_cli_path = kicad_directory / "kicad-cli"


def main():
    x = KicadProjectCreator(logging.DEBUG)


if __name__ == "__main__":
    main()
