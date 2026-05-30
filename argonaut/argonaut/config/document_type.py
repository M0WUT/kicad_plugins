# Standard imports
from dataclasses import dataclass
from pathlib import Path

# Third party imports

# Local imports


@dataclass(frozen=True)
class DocumentType:
    abbreviation: str
    description: str
    relative_path: Path
    separate_repo: bool = False

    def __lt__(self, other: "DocumentType") -> bool:
        return self.abbreviation < other.abbreviation


SUPPORTED_DOCUMENT_TYPES = sorted(
    [
        DocumentType(
            "REQ",
            "Requirements Specification",
            Path("requirements"),
            separate_repo=False,
        ),
        DocumentType("PCB", "KiCad PCB Project", Path("pcb"), separate_repo=True),
        DocumentType("SW", "Software Project", Path("software"), separate_repo=True),
        DocumentType("FW", "Firmware Project", Path("firmware"), separate_repo=True),
        DocumentType("RTL", "RTL Project", Path("rtl"), separate_repo=True),
        DocumentType("CAD", "Mechanical CAD part", Path("cad"), separate_repo=False),
    ]
)


def main():
    print(SUPPORTED_DOCUMENT_TYPES)


if __name__ == "__main__":
    main()
