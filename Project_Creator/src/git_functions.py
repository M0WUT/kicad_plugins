from pathlib import Path
import subprocess

from dataclasses import dataclass

from project_creator.src.file_operations import add_project_readme_header
from project_creator.src.gh_functions import run_shell_command
from ui import ask_question, show_error


try:
    from git import Repo
except ImportError:
    show_error(
        "Plugin requirements not installed. Please use Kicad Command Prompt and "
        f"`pip install -r {Path(__file__).parent.absolute()}/requirements.txt`",
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


def git_pull(local_folder: Path, show_error_window: bool = True):
    try:
        run_shell_command(["git", "-C", f"{local_folder}", "pull"])
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to pull changes to repo "{local_folder}"',
                "Git pull failed",
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

    git_commit_and_push(local_folder, "added README")


@dataclass
class GitInfo:
    local_path: Path
    upstream: str
    commit_hash: str
    uncommitted_local_changes: bool
    repos_out_of_sync: bool
    local_ahead_commit_count: int
    local_behind_commit_count: int


def get_git_info(path: Path) -> GitInfo:
    repo = Repo(path)
    commit_hash = repo.heads.main.commit.tree.hexsha
    repo.remote("origin").fetch()

    local_branch = repo.active_branch.name
    remote_branch = f"origin/{local_branch}"

    local_ahead_commit_count = sum(
        1 for c in repo.iter_commits(f"{remote_branch}..{local_branch}")
    )

    local_behind_commit_count = sum(
        1 for c in repo.iter_commits(f"{local_branch}..{remote_branch}")
    )

    # Get the local and remote commits for the active branch
    latest_local_commit = repo.head.commit.tree.hexsha
    latest_remote_commit = repo.remote("origin").refs["main"].commit.tree.hexsha

    # Diffs
    uncommitted_diffs = repo.index.diff(None)

    return GitInfo(
        local_path=path,
        upstream=repo.remotes.origin.url,
        commit_hash=commit_hash,
        uncommitted_local_changes=bool(uncommitted_diffs),
        repos_out_of_sync=bool(latest_remote_commit != latest_local_commit),
        local_ahead_commit_count=local_ahead_commit_count,
        local_behind_commit_count=local_behind_commit_count,
    )


def ensure_git_repo_up_to_date(path: Path) -> None:
    git_info = get_git_info(path)

    # Exit early if up to date
    if (
        git_info.repos_out_of_sync is False
        and git_info.uncommitted_local_changes is False
    ):
        return

    if git_info.uncommitted_local_changes:
        show_error(
            "Current repo has uncommitted local changes. "
            "Please either commit or add to gitignore",
            "Uncommitted local changes",
        )

    if git_info.local_ahead_commit_count > 0 and git_info.local_behind_commit_count > 0:
        show_error(
            "Local repo has diverged from remote. Please fix", "Diverged git repo"
        )

    if git_info.local_ahead_commit_count > 0:
        show_error(
            'There are local commits that have not been pushed to remote. Please run "git push" and retry',
            "Un-pushed local commits",
        )

    if git_info.local_behind_commit_count > 0:
        if ask_question(
            "Local repo behind remote. Do you wish to pull the remote changes?",
            "Pull remote changes?",
        ):
            git_pull(path)
            git_info = get_git_info(path)
            assert git_info.repos_out_of_sync is False

    raise NotImplementedError  # I don't know how we got here
