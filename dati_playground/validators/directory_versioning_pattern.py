import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

VERSION_PATTERN = r"(latest|v?\d+(\.\d+){0,2})$"  # Regular expression pattern to match versioning format
DIR_PATTERN = (
    r"(latest|\b(?:\D*\d\D*)+\b)"  # Regular expression pattern to match directory names
)


def is_leaf_directory(directory: Path) -> bool:
    """
    Checks if the directory does not contain any subdirectories.
    """
    for subdir in directory.iterdir():
        if subdir.is_dir():
            return False
    return True


def sibling_directories(directory: Path) -> list:
    """
    Retrieves a list of sibling directories at the same level as the specified directory.
    """
    parent_directory = directory.parent

    # all subdir
    subdirectories = []
    for subdir in parent_directory.iterdir():
        if subdir.is_dir():
            subdirectories.append(subdir)

    return subdirectories


def is_versioned_directory(directory: Path) -> bool:
    """
    Verifies if the name of the directory matches the versioned directory pattern.
    """
    return bool(re.match(DIR_PATTERN, directory.name))


def validate(fpath: Path, errors):
    """
    Validates the directory structure and naming conventions for versioned directories.
    """

    fpath_parent = Path(fpath.parent)
    # check if fpath is leaf and versioned dir
    if (
        not fpath_parent.is_dir()
        or not is_leaf_directory(fpath_parent)
        or not is_versioned_directory(fpath_parent)
        or fpath_parent.name == "latest"
    ):
        log.debug(f"'{fpath_parent.name}' in path '{fpath_parent}' is not checked")
        return True

    log.debug(f"{fpath_parent} is a leaf and versioned dir")
    sibling_dirs = sibling_directories(fpath_parent)

    # Remove 'latest' from sibling_dirs and check if there are more than one directory
    version_dirs = []
    for dir in sibling_dirs:
        if str(dir.name) != "latest":
            version_dirs.append(dir.name)
    if len(version_dirs) < 2:
        return True

    log.debug(f"Versioned directories to validate: {version_dirs}")

    # Verify that all version directories start with a number or "v"
    if not (
        all(re.match(r"v\d", version) for version in version_dirs)
        or all(version[0].isdigit() for version in version_dirs)
    ):
        log.debug(
            f"Inconsistent versioning pattern found for {fpath_parent}: {version_dirs}"
        )
        errors.append(
            f"Inconsistent versioning pattern found for {fpath_parent}: {version_dirs}"
        )
        return False

    # Verify that all version directories match the versioning pattern
    if not (all(re.match(VERSION_PATTERN, version) for version in version_dirs)):
        log.debug(f"Inconsistent versioning pattern found for {fpath}: {version_dirs}")
        errors.append(
            f"Inconsistent versioning pattern found for {fpath}: {version_dirs}"
        )
        return False

    return True
