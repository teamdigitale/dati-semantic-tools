#
# Validate .ttl files with pyshacl.
#
import logging
from pathlib import Path
from sys import argv

import jsonschema
import yaml

log = logging.getLogger(__name__)


def is_valid_jsonschema(f: Path):
    schema = yaml.safe_load(f.read_text())
    jsonschema.Draft7Validator.check_schema(schema)
    log.info(f"Valid json-schema in {f.absolute().as_posix()}")


if __name__ == "__main__":
    files = argv[1:]

    for f in files:
        if not f.endswith(".schema.yaml"):
            continue
        f = Path(f)
        is_valid_jsonschema(f)
