import os
import platform
import shutil
import stat
import subprocess
from enum import Enum, auto
from pathlib import Path
from typing import Callable


class OSType(Enum):
    Windows = auto()
    Linux = auto()


def get_os_type() -> OSType:
    os_type = platform.system()
    if os_type == "Windows":
        return OSType.Windows
    else:
        raise NotImplementedError


def get_kicad_path() -> Path:
    if get_os_type() == OSType.Windows:
        # Try local install
        home_directory = Path.home()
        test_directory = (
            home_directory / "AppData" / "Local" / "Programs" / "Kicad"
        )
        if test_directory.is_dir():
            installed_kicad_versions = [x for x in test_directory.iterdir()]
            if len(installed_kicad_versions) != 1:
                raise NotImplementedError("Multiple Kicad versions found")

            kicad_path = installed_kicad_versions[0] / "bin"
            return kicad_path
        else:
            raise NotImplementedError
    else:
        # Unknown OS
        raise NotImplementedError


def get_temp_path() -> Path:
    if get_os_type() == OSType.Windows:
        temp_directory = Path.home() / "AppData" / "Local"
        return temp_directory
    else:
        # Unknown OS
        raise NotImplementedError


def delete_folder(repo_path: Path) -> None:
    def overwrite_permissions(
        func: Callable, path: Path, *args, **kwargs
    ) -> None:
        # Need to overwrite permission for the .git folder
        # NB this makes this function quite dangerous
        os.chmod(path, stat.S_IWUSR)
        func(path)

    shutil.rmtree(repo_path, False, overwrite_permissions)
