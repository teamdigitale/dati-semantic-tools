import json
import logging
from functools import lru_cache
from pathlib import Path

import yaml
from rdflib import Graph

log = logging.getLogger(__name__)

MIME_JSONLD = "application/ld+json"
MIME_TURTLE = "text/turtle"


def is_recent_than(spath, dpath):
    if not dpath.exists():
        return True

    return dpath.stat().st_mtime <= spath.stat().st_mtime


@lru_cache(maxsize=128)
def parse_graph(vpath_ttl, format=MIME_TURTLE):
    log.info(f"Parsing file: {vpath_ttl}")
    g = Graph()
    g.parse(vpath_ttl, format=format)
    log.warning(f"Parsed file: {vpath_ttl}")
    return g


@lru_cache(maxsize=128)
def yaml_load(fpath):
    return yaml.safe_load(Path(fpath).read_text())


@lru_cache(maxsize=128)
def yaml_to_json(s: str):
    return json.dumps(yaml.safe_load(s), indent=2)
