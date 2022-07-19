#!/usr/bin/env python3
#
# CSV Validator with frictionless
#
import json
import logging
import re

log = logging.getLogger(__name__)

RE_FIELD = re.compile("^[a-zA-Z0-9_]{2,64}$")
from frictionless import validate_resource
from frictionless.report import Report


@Report.from_validate
def is_csv(fpath):
    """Expose validation results from frictionless."""

    errors = []

    report = validate_resource(fpath)
    current_errors = {}
    if not report.valid:
        current_errors = report.flatten(["rowPosition", "fieldPosition", "code"])
        log.error(f"Invalid file: {fpath}.")
        log.debug(json.dumps(current_errors, indent=2))
        errors.append({fpath.as_posix(): current_errors})
        raise ValueError(errors)

    for field_name in [
        field.name for tasks in report.tasks for field in tasks.resource.schema.fields
    ]:
        if not RE_FIELD.match(str(field_name)):
            log.error(f"Invalid field name: {field_name} in {fpath.name}")
            current_errors = {field_name: f"Invalid field name: {field_name}"}

    if current_errors:
        errors.append({fpath.as_posix(): current_errors})
        raise ValueError(errors)

    log.info(f"File {fpath} is valid")
    return report
