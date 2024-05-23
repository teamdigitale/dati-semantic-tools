import logging
from pathlib import Path

log = logging.getLogger(__name__)

required_subdirs = [
    "assets/controlled-vocabularies",
    "assets/ontologies",
    "assets/schemas",
]


def validate(fpath: Path, errors: list):
    """
    Validate directory structure to ensure required root directories exist.
    Check that the structure of the assets directories
    complies with required_subdirs.

    Args:
        fpath (Path): The path of the file from which to obtain The path of the root directory to check.

    """

    root_dir = Path(fpath.parts[0])

    if not root_dir.is_dir():
        log.warning(f"{root_dir} is not a directory.")
        return True

    subdirs = []
    for subdir in root_dir.iterdir():

        if subdir.is_dir():
            subdirs.append(str("/".join(subdir.parts)))

    # Check if all direct subdirectories are present in required_subdirs
    if set(subdirs) <= set(required_subdirs):
        return True
    else:
        # Find missing subdirectories
        missing_dirs = set(subdirs) - set(required_subdirs)

        if missing_dirs:
            log.debug(
                f"One or more directories do not conform to the expected structure in '{root_dir}' dir: {missing_dirs}"
            )
            errors.append(
                f"One or more directories do not conform to the expected structure in '{root_dir}' dir: {missing_dirs}"
            )

        return False
