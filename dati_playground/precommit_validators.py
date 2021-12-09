import logging
from functools import lru_cache
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

log = logging.getLogger(__name__)

MAX_DEPTH = 5
basedir = Path(__file__).parent


@lru_cache(maxsize=100)
def get_shacl_graph(absolute_path: str) -> Graph:
    if not Path(absolute_path).is_absolute():
        raise ValueError(f"{absolute_path} is not an absolute path")
    log.info(f"Loading SHACL graph from {absolute_path}")
    shacl_graph = Graph()
    shacl_graph.parse(absolute_path, format="turtle")
    return shacl_graph


def validate_shacl(file):
    log.info("Validating {}".format(file))
    shacl_graph = None
    rule_file_path = None
    rule_dir = Path(file).parent
    for _ in range(MAX_DEPTH):
        rule_file_candidate = rule_dir / "rules.shacl"
        if rule_file_candidate.exists():
            rule_file_path = rule_file_candidate.absolute().as_posix()
            shacl_graph = get_shacl_graph(rule_file_path)
            log.info(f"Found shacl file: {rule_file_path}")
            break
        if rule_dir == basedir:
            break
        rule_dir = rule_dir.parent
    try:
        is_valid, graph, report_text = validate(file, shacl_graph=shacl_graph)
        log.info(f"Validation result: {is_valid}, {rule_file_path}, {report_text}")
        if not is_valid:
            exit(1)
    except Exception as e:
        log.error(f"Error validating {file}: {rule_file_path} {e}")
        raise
