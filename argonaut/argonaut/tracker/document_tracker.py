# Standard imports
import json

# Third party imports

# Local imports
from argonaut.config.document_type import DocumentType
from argonaut.tracker.tracker import Tracker


class DocumentTracker(Tracker):

    def generate_next_number(self, document_type: DocumentType) -> int:
        assert (
            self.project_json is not None
        ), "Project JSON must be loaded before searching"
        try:
            current_documents = self.project_json["documents"][
                document_type.abbreviation.lower()
            ]

            current_document_numbers = [
                int(x.split("-")[-1]) for x in current_documents
            ]

            self.validate_item_numbers(current_document_numbers)
            return current_document_numbers[-1] + 1

        except KeyError:
            # No documents of expected type exist yet
            return 1

    def update(self, document_reference: str, info: dict[str, str]):
        try:
            self.project_json["documents"][self.document_type.abbreviation.lower()][
                document_reference
            ] = info
        except KeyError:
            self.project_json["documents"][self.document_type.abbreviation.lower()] = {}
            self.project_json["documents"][self.document_type.abbreviation.lower()][
                document_reference
            ] = info

        with open(self.absolute_json_path, "w") as file:
            json.dump(self.project_json, file, indent=4)

    def regenerate_readme(self):
        pass

    def set_document_type(self, document_type: DocumentType) -> None:
        self.document_type = document_type

    def get_item_names(self) -> list[str]:
        try:
            return [
                x["name"]
                for x in self.project_json[
                    str(self.document_type.relative_path)
                ].values()
            ]
        except KeyError:
            return []
