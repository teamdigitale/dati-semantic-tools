import logging
from pathlib import Path

import jsonschema
import yaml

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def validate(fpath: Path, errors: list):
    try:
        schema = yaml.safe_load(fpath.read_text())
    except yaml.YAMLError as e:
        log.debug(f"Failed to parse YAML file {fpath}: \n{e}")
        errors.append(f"Failed to parse YAML file {fpath}: \n{e}")
        return False

    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as e:
        log.debug(f"JSON Schema validation error on file {fpath}: \n{e}")
        errors.append(f"JSON Schema validation error on file {fpath}: \n{e}")
        return False
    except jsonschema.exceptions.ValidationError as e:
        log.debug(f"JSON Schema validation error on file {fpath}: \n{e}")
        errors.append(f"JSON Schema validation error on file {fpath}: \n{e}")
        return False
    except Exception as e:
        log.debug(
            f"Unexpected error during JSON Schema validation on file {fpath}: \n{e}"
        )
        errors.append(
            f"Unexpected error during JSON Schema validation on file {fpath}: \n{e}"
        )
        return False

    return True
