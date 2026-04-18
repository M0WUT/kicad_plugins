import subprocess
from pathlib import Path
from typing import Optional

from .os_functions import OSType, get_os_type


def run_shell_command(command: list[str]) -> str:
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


def github_project_exists(github_user: str, repo_name: str):
    try:
        run_shell_command(["gh", "repo", "view", f"{github_user}/{repo_name}"])
        return True
    except subprocess.CalledProcessError:
        return False


def get_current_github_user() -> Optional[str]:
    try:
        response = run_shell_command(["gh", "auth", "status"])
    except subprocess.CalledProcessError:
        return None
    # response will contain .... github.com account <Github User> ....
    gh_username = response.split("github.com account ")[1].split(" ")[0]
    return gh_username


def create_blank_github_repo(repo_name: str) -> bool:
    try:
        run_shell_command(["gh", "repo", "create", "--public", f"{repo_name}"])
        return True
    except subprocess.CalledProcessError:
        return False


def git_checkout(gh_user: str, repo_name: str, checkout_location: Path):
    run_shell_command(
        [
            "gh",
            "repo",
            "clone",
            f"{gh_user}/{repo_name}",
            f"{checkout_location.absolute()}",
        ],
    )


def git_push(repo_location: Path, commit_message: str):
    run_shell_command(["git", "-C", f"{repo_location}", "add", "."])
    run_shell_command(
        ["git", "-C", f"{repo_location}", "commit", "-m", f"{commit_message}"]
    )
    run_shell_command(["git", "-C", f"{repo_location}", "push"])


def main():
    get_current_github_user()


if __name__ == "__main__":
    main()
