from pathlib import Path
import subprocess

from dataclasses import dataclass

from .file_operations import add_project_readme_header
from .gh_functions import run_shell_command
from .ui import show_error


try:
    from git import Repo
except ImportError:
    show_error(
        f"Plugin requirements not installed. Please use Kicad Command Prompt and `pip install -r {Path(__file__).parent.absolute()}requirements.txt`",
        "Modules not installed",
    )


def git_commit_and_push(
    local_folder: Path,
    commit_message: str,
    show_error_window: bool = True,
):
    try:
        run_shell_command(["git", "-C", f"{local_folder}", "add", "."])
        run_shell_command(
            ["git", "-C", f"{local_folder}", "commit", "-m", f"{commit_message}"]
        )
        run_shell_command(["git", "-C", f"{local_folder}", "push"])
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to push to repo "{local_folder}"',
                "Git push failed",
            )


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

    run_shell_command(["git", "-C", f"{local_folder}", "add", "README.md"])
    run_shell_command(
        ["git", "-C", f"{local_folder}", "commit", "-m", "automatically created"]
    )
    run_shell_command(["git", "-C", f"{local_folder}", "branch", "-M", "main"])
    run_shell_command(["git", "-C", f"{local_folder}", "push", "-u", "origin", "main"])


@dataclass
class GitInfo:
    local_path: Path
    upstream: str
    commit_hash: str


def get_git_info(path: Path) -> GitInfo:
    repo = Repo(path)
    commit_hash = repo.heads.main.commit.tree.hexsha
    return GitInfo(
        local_path=path, upstream=repo.remotes.origin.url, commit_hash=commit_hash
    )
