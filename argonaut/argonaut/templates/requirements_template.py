# Standard imports
from pathlib import Path

# Third party imports

# Local imports
from argonaut.misc.git import generate_github_repo_url
from argonaut.config.document_type import DocumentType
from argonaut.creator.creator import generate_folder_name


def init_requirements_folder(
    local_path: Path,
    project_repo_owner: str,
    project_repo_name: str,
    document_type: DocumentType,
    document_reference: str,
    document_name: str,
    document_description: str,
) -> dict[str, str]:

    with open(local_path / f"{document_reference}.md", "w+") as file:
        file.write(f"{document_description}\n")

        file.write("# General\n")
        file.write("| Requirement ID | Requirement | Justification |\n")
        file.write("| --- | --- | --- |\n")
        file.write("| GEN-01 | Project must be awesome | obviously! |\n")

    return {
        "name": document_name,
        "description": document_description,
        "url": f"{generate_github_repo_url(project_repo_owner, project_repo_name)}/blob/main/{document_type.relative_path}/{generate_folder_name(document_reference, document_name)}/{document_reference}.md",  # noqa: E501
    }
