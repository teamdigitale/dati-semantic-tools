import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

# List of filenames to be excluded
EXCLUDED_FILENAMES = [
    "index.ttl",
    "datapackage.json",
    "context-short.ld.yaml",
    "rules.shacl",
    "latest",
]

# List of extensions to be excluded
EXCLUDED_EXTENSIONS = [
    ".md",
    ".shacl",
    ".frame.yamlld",
    ".ld.yaml",
    ".schema.yaml",
    ".example.yaml",
    ".example.ttl",
    ".png",
    ".html",
    ".xml",
    ".xsd",
]


def validate(fpath: Path, errors):

    if fpath.is_dir():
        log.debug(f"The dir '{fpath.name}' in path '{fpath}' is not checked")
        return True

    suffixes = fpath.suffixes
    extension = "".join(suffixes)
    filename = re.sub(extension, "", fpath.name)

    if (
        fpath.name in EXCLUDED_FILENAMES
        or extension in EXCLUDED_EXTENSIONS
        or fpath.name
    ):
        log.debug(f"The file '{fpath.name}' in path '{fpath}' is not checked")
        return True

    # Check the name of the file and parent directories
    path_dirs = fpath.parent

    if filename not in path_dirs.parts:
        log.debug(
            f"Filename '{fpath.name}' in path '{fpath}' does not match its containing directory name"
        )
        errors.append(
            f"Filename '{fpath.name}' in path '{fpath.as_posix()}' does not match its containing directory name"
        )
        return False

    return True
