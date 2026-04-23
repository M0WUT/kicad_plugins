import subprocess
from pathlib import Path
import logging

import wx

from .ui import show_error


def run_shell_command(command: list[str]) -> str:
    print(" ".join(command))
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


def check_github_project_exists(
    github_user: str, repo_name: str, show_error_window: bool = True
) -> bool:
    try:
        run_shell_command(["gh", "repo", "view", f"{github_user}/{repo_name}"])
        return True
    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Required Github project "{github_user}/{repo_name}" does not exist',
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
    gh_user: str,
    repo_name: str,
    clone_location: Path,
    show_error_window: bool = True,
) -> bool:
    try:
        run_shell_command(
            [
                "gh",
                "repo",
                "clone",
                f"{gh_user}/{repo_name}",
                f"{clone_location.absolute()}",
            ],
        )
        return True

    except subprocess.CalledProcessError:
        if show_error_window:
            show_error(
                f'Failed to clone repo "{gh_user}/{repo_name}" to '
                f'"{clone_location.absolute()}"',
                "Git clone failed",
            )
        return False


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


def main():
    _ = wx.App()
    print(get_current_github_user())


if __name__ == "__main__":
    main()
