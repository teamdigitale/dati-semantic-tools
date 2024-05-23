import logging
from functools import lru_cache
from pathlib import Path

from pyshacl import validate as pyshacl_validate
from rdflib import Graph

log = logging.getLogger(__name__)

MAX_DEPTH = 5
basedir = Path(__file__).parent


@lru_cache(maxsize=100)
def get_shacl_graph(absolute_path: str) -> Graph:
    if not Path(absolute_path).is_absolute():
        raise ValueError(f"{absolute_path} is not an absolute path")
    log.debug(f"Loading SHACL graph from {absolute_path}")
    shacl_graph = Graph()
    shacl_graph.parse(absolute_path, format="turtle")
    return shacl_graph


def validate(fpath: Path, errors: list):
    log.debug("Validating {}".format(fpath))
    shacl_graph = None
    rule_file_path = None
    rule_dir = fpath.parent
    for _ in range(MAX_DEPTH):
        rule_file_candidate = rule_dir / "rules.shacl"
        if rule_file_candidate.exists():
            rule_file_path = rule_file_candidate.absolute().as_posix()
            shacl_graph = get_shacl_graph(rule_file_path)
            log.debug(f"Found shacl file: {rule_file_path}")
            break
        if rule_dir == basedir:
            break
        rule_dir = rule_dir.parent
    try:
        # Enable advanced shacl validation: https://www.w3.org/TR/shacl-af/
        is_valid, graph, report_text = pyshacl_validate(
            fpath.as_posix(), shacl_graph=shacl_graph, advanced=True
        )
        log.debug(
            f"Validation result: {fpath}, {is_valid}, {rule_file_path}, {report_text}"
        )
        if not is_valid:
            errors.append(f"The file '{fpath}' is not valid: {report_text}")
            return False
        return True
    except Exception as e:
        log.debug(f"Error validating {fpath}: {rule_file_path} {e}")
        errors.append(f"Error validating {fpath}: {rule_file_path} {e}")
        # raise
        return False
