import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

pattern = r"^[\\.a-z0-9_-]{2,64}$"
extensions_to_check = [".ttl", ".rdf", ".csv", ".yaml"]


def validate(fpath: Path, errors: list):

    # Check if the file has a extension to check
    if fpath.suffix not in extensions_to_check:
        log.debug(f"The file '{fpath}' does not have a extension to check")
        return True

    # Check the name of the file and parent directories
    dirs = [fpath.parent] + list(fpath.parents)[
        :2
    ]  # Get up to 3 levels of parent directories
    for dir_path in dirs:
        dir_name = dir_path.name
        if not re.match(pattern, dir_name):
            log.debug(
                f"The name of the directory '{dir_name}' in path '{dir_path}' does not match the required pattern"
            )
            errors.append(
                f"The name of the directory '{dir_name}' in path '{dir_path}' does not match the required pattern"
            )

    # Check the name of the file
    if not re.match(pattern, fpath.stem):
        log.debug(
            f"The name of the file '{fpath.name}' in path '{fpath.parent}' does not match the required pattern"
        )
        errors.append(
            f"The name of the file '{fpath.name}' in path '{fpath.parent}' does not match the required pattern"
        )

    if errors:
        return False

    return True
