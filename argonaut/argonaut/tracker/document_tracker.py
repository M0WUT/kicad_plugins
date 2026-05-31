# Standard imports
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json

# Third party imports

# Local imports
from argonaut.gui.dialog import ask_question, show_error
from argonaut.config.document_type import DocumentType
from argonaut.misc.git import git_clone
from argonaut.misc.os import delete_folder, get_temp_dir_path
from argonaut.logger.logger import create_default_logger
from argonaut.config.config import PROJECT_JSON_PATH
from argonaut.tracker.tracker import Tracker


class DocumentTracker(Tracker):

    def generate_next_document_number(self, document_type: DocumentType) -> int:
        assert (
            self.project_json is not None
        ), "Project JSON must be loaded before searching"
        current_document_of_type = self.project_json["documents"][
            document_type.abbreviation
        ]
