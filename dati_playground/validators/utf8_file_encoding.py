import logging
from pathlib import Path

log = logging.getLogger(__name__)

EXCLUDED_EXTENSIONS = [".md", ".png"]


def validate(fpath: Path, errors: list):
    """
    Verifies if the specified file is encoded in UTF-8.
    """

    log.debug(f"Validating {fpath}")

    # check if fpath is not a file
    if fpath.is_dir() or fpath.name.endswith(tuple(EXCLUDED_EXTENSIONS)):
        log.debug(f"'{fpath.name}' in path '{fpath}' is not checked")
        return True

    try:
        with open(fpath, "r", encoding="utf-8") as file:
            _ = file.read()
        log.debug(f"The file '{fpath}' is encoded in UTF-8")
        return True
    except UnicodeDecodeError:
        errors.append(f"The file '{fpath}' is not encoded in UTF-8")
        return False
