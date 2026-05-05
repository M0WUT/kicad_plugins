from pathlib import Path


def add_project_readme_header(
    readme_path: Path, project_number: int, project_name: str, project_description: str
):
    with open(readme_path, "w+") as readme_file:
        readme_file.write(f"# P{project_number:04d} - {project_name}\n")
        readme_file.write(f"{project_description}\n")
