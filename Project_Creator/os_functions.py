import os
import platform
import shutil
import stat
from enum import Enum, auto
from pathlib import Path
from typing import Callable

from .config import TEMP_FOLDER_NAME


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
        test_directory = home_directory / "AppData" / "Local" / "Programs" / "Kicad"
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


def get_temp_dir_path(create_folder: bool = True) -> Path:
    if get_os_type() == OSType.Windows:
        temp_directory = Path.home() / "AppData" / "Local" / TEMP_FOLDER_NAME
    else:
        # Unknown OS
        raise NotImplementedError

    if create_folder:
        temp_directory.mkdir(exist_ok=True, parents=True)
    return temp_directory


def delete_folder(repo_path: Path) -> None:
    def overwrite_permissions(func: Callable, path: Path, *args, **kwargs) -> None:
        # Need to overwrite permission for the .git folder
        # NB this makes this function quite dangerous
        os.chmod(path, stat.S_IWUSR)
        func(path)

    shutil.rmtree(repo_path, False, overwrite_permissions)


def copy_into(src: Path, dst: Path) -> Path:
    """
    Recursively copy src directory into dst directory.

    - Fails if any file or directory already exists in dst
    - No overwrites allowed
    - No symlinks assumed
    - OS-agnostic
    """

    src = Path(src)
    dst = Path(dst)

    if not src.is_dir():
        raise ValueError(f"src must be a directory: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        target = dst / item.name

        if target.exists():
            raise FileExistsError(f"Target already exists: {target}")

        if item.is_dir():
            copy_into(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    return dst
