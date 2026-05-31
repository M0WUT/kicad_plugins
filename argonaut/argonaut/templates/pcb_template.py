# Standard imports
from contextlib import suppress
from pathlib import Path
import json

# Third party imports

# Local imports
from argonaut.tracker.project_tracker import ProjectTracker
from argonaut.misc.git import (
    add_github_secret,
    copy_files_from_git_repo,
    generate_github_pages_url,
    generate_github_repo_url,
    set_github_pages_source_to_actions,
)
from argonaut.config.document_type import DocumentType
from argonaut.config.config import (
    GITHUB_PAGES_DEPLOYMENT_WORKFLOW_NAME,
    KICAD_TEMPLATE_REPO_OWNER,
    KICAD_TEMPLATE_REPO_NAME,
    KICAD_RELEASER_REPO_OWNER,
    KICAD_RELEASER_REPO_NAME,
    PROJECT_TRACKER_JSON_PATH,
    PROJECT_TRACKER_REPO_NAME,
    PROJECT_TRACKER_REPO_OWNER,
)
from argonaut.config.repo_secrets import REPO_SECRETS


def init_pcb_folder(
    local_path: Path,
    repo_owner: str,
    repo_name: str,
    document_type: DocumentType,
    document_reference: str,
    document_name: str,
    document_description: str,
) -> dict[str, str]:

    # Add README
    readme_path = local_path / "README.md"
    with open(readme_path, "w+") as readme_file:
        readme_file.write(f"# {document_reference} - {document_name}\n")
        readme_file.write(f"{document_description}\n")

    # Copy over template project
    copy_files_from_git_repo(
        KICAD_TEMPLATE_REPO_OWNER,
        KICAD_TEMPLATE_REPO_NAME,
        local_path,
        exclude_paths=[Path("README.md")],
    )

    # Rename files
    str_to_replace = KICAD_TEMPLATE_REPO_NAME
    new_file_stem = document_reference
    for file in local_path.rglob(f"{str_to_replace}*"):
        file.rename(file.parent / f"{new_file_stem}{file.suffix}")

    # Replace text content in files
    for path in local_path.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            with suppress(UnicodeDecodeError):
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace(str_to_replace, new_file_stem),
                    encoding="utf-8",
                )
    # Copy Github actions folder
    copy_files_from_git_repo(
        KICAD_RELEASER_REPO_OWNER,
        KICAD_RELEASER_REPO_NAME,
        local_path,
        include_paths=[Path("github")],
    )
    (local_path / "github").rename(local_path / ".github")

    # Copy secrets over
    for secret_name, secret_value in REPO_SECRETS.items():
        add_github_secret(repo_owner, repo_name, secret_name, secret_value)

    # Enable workflow as Github pages source
    set_github_pages_source_to_actions(repo_owner, repo_name)

    # Replace project text strings

    with ProjectTracker(
        PROJECT_TRACKER_REPO_OWNER, PROJECT_TRACKER_REPO_NAME, PROJECT_TRACKER_JSON_PATH
    ) as project_tracker:
        project_name = project_tracker.get_name_from_reference(
            document_reference.split("-")[0]
        )

    kicad_project_file_paths = list(local_path.rglob("*.kicad_pro"))
    assert len(kicad_project_file_paths) == 1, "Multiple kicad project files found"
    with open(kicad_project_file_paths[0]) as project_file:
        kicad_json = json.load(project_file)

        project_text_variables = {
            "WUT_BOARD_NAME": document_name,
            "WUT_BOARD_NUMBER": document_reference[-3:],
            "WUT_COMPANY": repo_owner,
            "WUT_GITHUB_PAGES_URL": generate_github_pages_url(
                repo_owner, repo_name
            ),  # noqa: E501
            "WUT_GITHUB_URL": generate_github_repo_url(
                repo_owner, repo_name
            ),  # noqa: E501
            "WUT_GIT_COMMIT_DATE": "",
            "WUT_GIT_COMMIT_TIME": "",
            "WUT_GIT_COMMIT_TAG": "",
            "WUT_GIT_VERSION": "",
            "WUT_LAYOUT_VERSION": "1",
            "WUT_PROJECT_NAME": project_name,
            "WUT_PROJECT_NUMBER": f"{document_reference[1:5]}",
            "WUT_RELEASE_STATUS": "DRAFT",
            "WUT_SCHEMATIC_VERSION": "1",
        }

    kicad_json["text_variables"] = project_text_variables

    with open(kicad_project_file_paths[0], "w") as project_file:
        json.dump(kicad_json, project_file, indent=4)

    return {
        "name": document_name,
        "description": document_description,
        "url": generate_github_repo_url(repo_owner, repo_name),
        "github_pages_url": generate_github_pages_url(repo_owner, repo_name),
    }


def create_pcb_readme_table(readme_file, docs: dict[str, str]):
    # Special handler for PCB
    readme_file.write(
        "| Reference | Name | Description | Repo URL | Github Pages Status | Image | Github Pages URL |\n"  # noqa: E501
    )
    readme_file.write(("| ---" * 7) + "|\n")
    for doc_reference, doc in docs.items():
        readme_file.write(
            f"| {doc_reference} | {doc['name']} | {doc['description']} | [Link]({doc['url']}) | ![Github Pages deployment]({doc['url']}/actions/workflows/{GITHUB_PAGES_DEPLOYMENT_WORKFLOW_NAME}/badge.svg) | ![Board image]({doc['github_pages_url']}/{doc_reference}-front.png) | [Link]({doc['github_pages_url']}) |\n"  # noqa: E501
        )
