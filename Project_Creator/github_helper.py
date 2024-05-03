import subprocess


def check_if_github_cli_exists():
    try:
        subprocess.check_output(
            [
                "gh",
                "--version",
            ]
        )
        return True
    except FileNotFoundError:
        return False


def check_if_project_exists(github_user: str, repo_name: str):
    try:
        subprocess.check_output(
            ["gh", "repo", "view", f"{github_user}/{repo_name}"],
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_current_github_user() -> str:
    response = subprocess.check_output(["gh", "auth", "status"])
    response = response.decode()
    # response will contain .... github.com account <Github User> ....
    gh_username = response.split("github.com account ")[1].split(" ")[0]
    return gh_username

def create_blank_github_repo(repo_name: str):
    try:
        subprocess.check_output(
            ["gh", "repo", "create", "--public", f"{repo_name}"]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    get_current_github_user()


if __name__ == "__main__":
    main()
