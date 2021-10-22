import json
from pathlib import Path

import yaml

MIME_JSONLD = "application/ld+json"
MIME_TURTLE = "text/turtle"


def yaml_load(fpath):
    return yaml.safe_load(Path(fpath).read_text())


def yaml_to_json(s: str):
    return json.dumps(yaml.safe_load(s), indent=2)
