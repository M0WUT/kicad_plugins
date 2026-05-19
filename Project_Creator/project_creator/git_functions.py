# Standard imports
from pathlib import Path
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional

# Third party imports

# Local imports
from project_creator.os_functions import (
    OSType,
    copy_into,
    delete_folder,
    get_os_type,
    get_temp_dir_path,
)
from project_creator.ui import ask_question, get_folder_input, show_error

# Third party but need to load the show_error method first
try:
    from git import Repo
except ImportError:
    show_error(
        "Plugin requirements not installed. Please use Kicad Command Prompt and "
        f"`pip install -r {Path(__file__).parent.absolute()}/requirements.txt`",
        "Modules not installed",
    )


@dataclass
class GitInfo:
    local_path: Path
    upstream: str
    repo_owner: str
    repo_name: str
    commit_hash: str
    uncommitted_local_changes: bool
    repos_out_of_sync: bool
    local_ahead_commit_count: int
    local_behind_commit_count: int


def run_shell_command(command: list[str]) -> str:
    # print(" ".join(command))
    if get_os_type() == OSType.Windows:
        response = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).stdout
    else:
        response = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).stdout
    return response.decode()


def github_cli_exists():
    try:
        run_shell_command(["gh", "--version"])
        return True
    except FileNotFoundError:
        return False


def check_github_repo_exists(
    repo_owner: str, repo_name: str, show_error_window_if_not_exists: bool = True
) -> bool:
    try:
        run_shell_command(["gh", "repo", "view", f"{repo_owner}/{repo_name}"])
        return True
    except subprocess.CalledProcessError:
        if show_error_window_if_not_exists:
            show_error(
                f'Required Github project "{repo_owner}/{repo_name}" does not exist',
                "Repo not found",
            )
        return False


def get_current_github_user(show_error_window: bool = True) -> str:
    try:
        response = run_shell_command(["gh", "auth", "status"])
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error("GH tool not authorised as a user", "GH not authorised")
        return ""
    # response will contain .... github.com account <Github User> ....
    gh_username = response.split("github.com account ")[1].split(" ")[0]
    return gh_username


def create_blank_github_repo(repo_name: str, show_error_window: bool = True) -> bool:
    try:
        run_shell_command(["gh", "repo", "create", "--public", f"{repo_name}"])
        return True
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to create repo "{repo_name}" on Github',
                "Github repo creation failed",
            )
        return False


def git_clone(
    repo_owner: str,
    repo_name: str,
    clone_location: Path,
    create_dir: bool = True,
    check_existence_before_clone: bool = True,
    show_error_window: bool = True,
) -> bool:

    if create_dir:
        clone_location.mkdir(parents=True)

    if check_existence_before_clone:
        check_github_repo_exists(repo_owner, repo_name)

    try:
        run_shell_command(
            [
                "gh",
                "repo",
                "clone",
                f"{repo_owner}/{repo_name}",
                f"{clone_location.absolute()}",
            ],
        )
        return True

    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to clone repo "{repo_owner}/{repo_name}" to '
                f'"{clone_location.absolute()}"',
                "Git clone failed",
            )
        return False


def git_clone_interactive(
    repo_owner: str, repo_name: str, local_folder_name: Optional[str] = None
) -> Path:

    if local_folder_name is None:
        local_folder_name = repo_name

    parent_folder = get_folder_input("Select location for local clone of repo")
    while not parent_folder.exists():
        show_error(
            f'Requested checkout folder "{parent_folder.absolute()}" does not exist',
            "Folder does not exist",
            exit_on_error=False,
        )
        parent_folder = get_folder_input("Select location for local clone of repo")

    local_folder = parent_folder / local_folder_name
    git_clone(repo_owner, repo_name, local_folder)
    return local_folder


def validate_github_setup() -> str:
    # Check if Github CLI is present
    if github_cli_exists() is False:
        show_error(
            "Github CLI not found. Please ensure it is installed",
            "Github CLI not found",
        )

    # Query for Github user
    gh_user = get_current_github_user()
    if gh_user is None:
        show_error(
            "Github CLI is not authenticated as a user",
            "Github CLI not authenticated",
        )

    return gh_user


def git_commit_and_push(
    local_folder: Path,
    commit_message: str,
    show_error_window: bool = True,
):
    try:
        run_shell_command(["git", "-C", f"{local_folder}", "add", "."])
        run_shell_command(
            [
                "git",
                "-C",
                f"{local_folder}",
                "commit",
                "-m",
                f"Kicad PLUGIN: {commit_message}",
            ]
        )
        run_shell_command(["git", "-C", f"{local_folder}", "push"])
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to push to repo "{local_folder}"',
                "Git push failed",
            )


def git_add_explicit_path(
    repo_folder: Path, paths_to_add: list[Path], show_error_window: bool = True
):
    for path in paths_to_add:
        try:
            run_shell_command(
                ["git", "-C", f"{repo_folder}", "add", str(path.absolute())]
            )
        except subprocess.CalledProcessError:
            if show_error_window:
                show_error(
                    f'Failed to add path "{path.absolute}" to repo "{repo_folder}"',
                    "Git add failed",
                )


def git_add_submodule(
    local_folder: Path,
    submodule_folder: Path,
    submodule_upstream_url: str,
    show_error_window: bool = True,
):
    try:
        run_shell_command(
            [
                "git",
                "-C",
                f"{local_folder}",
                "submodule",
                "add",
                submodule_upstream_url,
                str(submodule_folder),
            ]
        )

        run_shell_command(
            [
                "git",
                "-C",
                f"{local_folder}",
                "config",
                "-f",
                ".gitmodules",
                f"submodule.{str(submodule_folder)}.branch",
                "main",
            ]
        )

    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to add submodule "{submodule_upstream_url}" '
                f'to repo "{local_folder}"',
                "Git add failed",
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


def git_pull_including_submodules(local_folder: Path, show_error_window: bool = True):
    try:
        run_shell_command(
            ["git", "-C", f"{local_folder}", "pull", "--recurse-submodules"]
        )
        run_shell_command(
            [
                "git",
                "-C",
                f"{local_folder}",
                "submodule",
                "update",
                "--init",
                "--recursive",
            ]
        )
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to pull changes to repo "{local_folder}"',
                "Git pull failed",
            )


def git_checkout(local_folder: Path, branch_name: str, show_error_window: bool = True):
    try:
        run_shell_command(["git", "-C", f"{local_folder}", "checkout", branch_name])

    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to checkout branch "{branch_name}" in repo "{local_folder}"',
                "Git checkout failed",
            )


def get_git_info(path: Path) -> GitInfo:
    repo = Repo(path)

    upstream_url = repo.remotes.origin.url

    github_repo_owner, github_repo_name = get_repo_owner_name_from_url(upstream_url)

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
        upstream=upstream_url,
        repo_owner=github_repo_owner,
        repo_name=github_repo_name,
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
            "There are local commits that have not been pushed to remote. "
            'Please run "git push" and retry',
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
        else:
            show_error(
                'Local repo is behind remote. Please run "git pull" and retry',
                "Un-pulled remote commits",
            )

    raise NotImplementedError  # I don't know how we got here


def copy_files_from_git_repo(
    repo_owner: str,
    repo_name: str,
    local_dest_path: Path,
    include_paths: Optional[list[Path]] = None,
    exclude_paths: Optional[list[Path]] = None,
):
    assert not (
        include_paths is not None and exclude_paths is not None
    ), "Only one of include and exclude paths can be specified"

    try:
        temp_clone_path = get_temp_dir_path() / repo_name
        git_clone(repo_owner, repo_name, temp_clone_path)

        delete_folder(temp_clone_path / ".git")

        if include_paths is not None:
            for path in include_paths:
                full_src_path = temp_clone_path / path
                full_dest_path = local_dest_path / path

                if full_src_path.is_dir():
                    full_dest_path.mkdir(exist_ok=True, parents=True)
                    copy_into(full_src_path, full_dest_path)
                else:
                    full_dest_path.parent.mkdir(exist_ok=True, parents=True)
                    shutil.copy(full_src_path, full_dest_path)

        else:
            if exclude_paths is not None:
                for path in exclude_paths:
                    full_path = temp_clone_path / path
                    if full_path.is_dir():
                        delete_folder(full_path)
                    else:
                        full_path.unlink()

            copy_into(temp_clone_path, local_dest_path)

    finally:
        delete_folder(temp_clone_path)


def add_github_secret(
    repo_owner: str,
    repo_name: str,
    secret_name: str,
    secret_value: str,
    show_error_window: bool = True,
) -> None:
    try:
        run_shell_command(
            [
                "gh",
                "secret",
                "set",
                secret_name,
                "--repo",
                f"{repo_owner}/{repo_name}",
                "--body",
                f'"{secret_value}"',
            ],
        )
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to add secret to repo "{repo_owner}/{repo_name}"',
                "Adding repo secret failed",
            )


def set_github_pages_source_to_actions(
    repo_owner: str, repo_name: str, show_error_window: bool = True
) -> None:
    try:
        for method in ["POST", "PUT"]:
            run_shell_command(
                [
                    "gh",
                    "api",
                    "--method",
                    method,
                    f"/repos/{repo_owner}/{repo_name}/pages",
                    "-f",
                    "build_type=workflow",
                ],
            )

    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                "Failed to change Github pages source for repo "
                f'"{repo_owner}/{repo_name}"',
                "Changing Github pages source failed",
            )


def generate_github_repo_url(repo_owner: str, repo_name: str) -> str:
    return f"https://github.com/{repo_owner.lower()}/{repo_name.lower()}"


def generate_github_pages_url(repo_owner: str, repo_name: str) -> str:
    return f"https://{repo_owner.lower()}.github.io/{repo_name.lower()}"


def get_repo_owner_name_from_url(url: str) -> tuple[str, str]:
    # URL may either be of the format git@github.com:M0WUT/p0003_wild-bull
    # or https://github.com/M0WUT/p0003_wild-bull.git

    repo_info = url.split("github.com")[1]
    # Remove first character (either : or /)
    repo_info = repo_info[1:]

    repo_owner, repo_name = repo_info.split("/")

    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    return repo_owner, repo_name


if __name__ == "__main__":
    print(get_git_info(Path(__file__).parent.parent))
