from pathlib import Path

from .git_functions import git_commit_and_push


def add_project_readme_header(
    readme_path: Path, project_number: int, project_name: str, project_description: str
):
    with open(readme_path, "w+") as readme_file:
        readme_file.write(f"# P{project_number:04d} - {project_name}\n")
        readme_file.write(f"{project_description}\n")


def add_basic_project_readme(
    project_number: int,
    project_name: str,
    project_description: str,
    local_folder: Path,
):
    readme_path = local_folder / "README.md"
    add_project_readme_header(
        readme_path, project_number, project_name, project_description
    )

    git_commit_and_push(local_folder, "added README")
