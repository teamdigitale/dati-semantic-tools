#!/usr/bin/env python3
#
# CSV Validator with frictionless
#
import json
import logging
import re

log = logging.getLogger(__name__)

RE_FIELD = re.compile("^[a-zA-Z0-9_]{2,64}$")
from frictionless import Package, Resource


def _get_resource(fpath):
    datapackage_candidates = (
        fpath.parent / f"datapackage.{ext}" for ext in ["json", "yaml", "yml"]
    )
    for datapackage in (d for d in datapackage_candidates if d.exists()):
        package = Package(datapackage)
        log.debug(f"Found {datapackage} in {fpath.parent}")
        for r in package.resources:
            if r.path == fpath.name:
                log.warning(f"Loading metadata for {r.path} from {datapackage.name}.")
                return r

    return Resource(fpath)


def is_csv(fpath):
    """Expose validation results from frictionless.

    If you need to use the validation results, you can
    decorate this function with `@Report.from_validate`
    """
    errors = []
    resource = _get_resource(fpath)
    report = resource.validate()
    current_errors = {}
    if not report.valid:
        current_errors = report.flatten(["rowPosition", "fieldPosition", "code"])
        log.error(f"Invalid file: {fpath}.")
        log.debug(json.dumps(current_errors, indent=2))
        errors.append({fpath.as_posix(): current_errors})

    #
    # Check further requirements.
    #
    for field_name in [
        field.name for tasks in report.tasks for field in tasks.resource.schema.fields
    ]:
        if not RE_FIELD.match(str(field_name)):
            log.error(
                f"Invalid field name for publication: {field_name} in {fpath.name}"
            )
            current_errors = {
                field_name: f"Invalid field name for publication: {field_name}"
            }

    if current_errors:
        errors.append({fpath.as_posix(): current_errors})
        raise ValueError(errors)

    log.info(f"File is valid: {fpath}")
    return report
