#!/usr/bin/env python3
#
# CSV Validator with frictionless
#
import json
import logging
import re
from pathlib import Path
from typing import Tuple

log = logging.getLogger(__name__)

RE_FIELD = re.compile("^[a-zA-Z0-9_]{2,64}$")
from frictionless import Package, Resource
from frictionless import validate as frictionless_validate


def _get_resource(fpath) -> Tuple[Package, Resource]:
    datapackage_candidates = (
        fpath.parent / f"datapackage.{ext}" for ext in ["json", "yaml", "yml"]
    )
    for datapackage in (d for d in datapackage_candidates if d.exists()):
        package = Package(datapackage)
        log.debug(f"Found {datapackage} in {fpath.parent}")
        for r in package.resources:
            if r.path == fpath.name:
                log.info(f"Loading metadata for {r.path} from {datapackage.name}.")
                return package, r

    return None, Resource(fpath)


def validate(fpath: Path, errors: list):
    """Expose validation results from frictionless.

    If you need to use the validation results, you can
    decorate this function with `@Report.from_validate`
    """
    package, resource = _get_resource(fpath)

    if package:
        report = resource.validate()
    else:
        report = frictionless_validate(fpath)

    # report = resource.f_validate()
    current_errors = []
    if not report.valid:
        current_errors = report.flatten(["message"])
        log.debug(f"Invalid file: {fpath}.")
        log.debug(json.dumps(current_errors, indent=1))

    #
    # Test field names if a datapackage is not defined.
    #
    if not package:
        for field_name in [
            field
            for tasks in report.tasks
            for field in tasks.labels
            if not RE_FIELD.match(str(field))
        ]:
            log.debug([f"Invalid field name for publication: {field_name}"])
            current_errors.append([f"Invalid field name for publication: {field_name}"])

    # Flat the nested list to a single list
    flat_errors = [error[0] for error in current_errors]

    # Convert the list to a string
    errors_string = "\n\t" + "\n\t".join(flat_errors)

    if current_errors:
        log.debug(f"Invalid file: {fpath.as_posix()}: {errors_string}")
        errors.append(f"Invalid file: {fpath.as_posix()}: {errors_string}")
        return False

    log.debug(f"File is valid: {fpath}")
    return True
