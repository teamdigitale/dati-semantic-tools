import logging
from pathlib import Path

log = logging.getLogger(__name__)


def is_leaf_directory(directory: Path) -> bool:
    """
    Checks if the directory does not contain any subdirectories.
    """
    for subdir in directory.iterdir():
        if subdir.is_dir():
            return False
    return True


def validate(fpath: Path, errors):
    """
    Checks if the directory containing the given file is a leaf directory and contains at least one turtle (.ttl) file.
    If the directory path contains 'schemas', it also verifies the presence of .oas3.yaml and index.ttl files.
    """

    directory = fpath.parent

    if not is_leaf_directory(directory):
        log.debug(f"'{directory.name}' in path '{directory}' is not a leaf directory")
        return True

    has_turtle_file = any(
        file.suffix == ".ttl" for file in directory.iterdir() if file.is_file()
    )
    if not has_turtle_file:
        log.debug(
            f"Leaf directory '{directory}' does not contain any turtle (.ttl) file"
        )
        errors.append(
            f"Leaf directory '{directory}' does not contain any turtle (.ttl) file"
        )
        return False

    # Additional check for directories containing 'schemas'
    if "schemas" in directory.parts:
        has_oas3_yaml_file = any(
            file.name.endswith(".oas3.yaml")
            for file in directory.iterdir()
            if file.is_file()
        )
        if not has_oas3_yaml_file:
            log.debug(
                f"The 'schemas' directory '{directory}' does not contain a .oas3.yaml file"
            )
            errors.append(
                f"The 'schemas' directory '{directory}' does not contain a .oas3.yaml file"
            )
            return False

        # Check if there is a file named 'index.ttl'
        has_index_ttl = any(
            file.name == "index.ttl" for file in directory.iterdir() if file.is_file()
        )
        if not has_index_ttl:
            log.debug(
                f"The 'schemas' directory '{directory}' does not contain any 'index.ttl' file"
            )
            errors.append(
                f"The 'schemas' directory '{directory}' does not contain any 'index.ttl' file"
            )
            return False

    return True
