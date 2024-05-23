import logging
from pathlib import Path

import yaml
from openapi_spec_validator import validate_spec

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def validate(fpath: Path, errors: list):
    content = fpath.read_text()
    try:
        spec_dict = yaml.safe_load(content)
    except yaml.YAMLError as e:
        log.debug(f"Failed to parse YAML file {fpath} \n{e}")
        errors.append(f"Failed to parse YAML file {fpath} \n{e}")
        return False

    try:
        # If no exception is raised by validate_spec(), the spec is valid.
        validate_spec(spec_dict)
    except Exception as e:
        log.debug(f"OpenAPI validation error of file {fpath} \n {e}")
        errors.append(f"OpenAPI validation error of file {fpath} \n {e}")
        return False

    return True
