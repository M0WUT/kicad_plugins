# Standard imports
import re

# Third party imports

# Local imports


class ProjectCreator:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    @classmethod
    def is_valid_project_repo_name(cls, name: str) -> bool:
        """
        Takes a candiate Github repo name and returns True
        if it matches the format that this tool creates
        """
        pattern = re.compile(r"^p\d{4}-\d{3}_[a-z]+(?:-[a-z]+)*$")
        return pattern.fullmatch(name) is not None
