# Standard imports
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

# Third party imports

# Local imports


@dataclass(frozen=True)
class DocumentType:
    abbreviation: str
    description: str
    relative_path: Path
    separate_repo: bool
    # Takes local path to create, project_repo_owner, project_repo_name, document_type, document_reference, document_name, documnet_description,  # noqa: E501
    init_function: Callable[
        [Path, str, str, "DocumentType", str, str, str], dict[str, str]
    ]
    # separate_repo: bool = False

    def __lt__(self, other: "DocumentType") -> bool:
        return self.abbreviation < other.abbreviation
