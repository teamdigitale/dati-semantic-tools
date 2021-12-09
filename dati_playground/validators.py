import os
from pathlib import Path
from typing import Dict

import jsonschema
import yaml
from openapi_spec_validator import validate_spec
from rdflib import Graph

from .utils import MIME_JSONLD, MIME_TURTLE, yaml_to_json


def true(*a, **kw):
    return True


def is_jsonschema(content: str):
    jsonschema.Draft7Validator.check_schema(yaml.safe_load(content))

    return True


def is_openapi(content: str):
    spec_dict = yaml.safe_load(content)

    # If no exception is raised by validate_spec(), the spec is valid.
    validate_spec(spec_dict)

    return True


def is_jsonld(content: str):
    content = yaml_to_json(content)
    g = Graph()
    g.parse(data=content, format=MIME_JSONLD)
    return True


def is_turtle(content: str):
    g = Graph()
    g.parse(data=content, format=MIME_TURTLE)
    return True


def is_framing_context(content: str):
    is_jsonld(content)
    return True
    data = yaml.safe_load(content)

    framing_context_schema = {
        "type": "object",
        "required": ["@context", "_meta"],
        "properties": {
            "@context": {
                "type": "object",
                "required": ["key"],
                "properties": {"key": {"type": "object"}},
            },
            "_meta": {
                "type": "object",
                "required": ["index"],
                "properties": {"index": {"type": "string"}},
            },
        },
    }
    jsonschema.validate(data, framing_context_schema)
    return True


def is_valid_sqlite(datafile: Path, schema: Dict) -> bool:
    """Load a sqlite datafile and verify that all entries are
        compliant with the given schemas.
    """
    raise NotImplementedError


VALID_SUFFIXES = {
    "*.ttl": is_turtle,
    "*.shacl": is_turtle,
    "*.ld.yaml": is_jsonld,
    "*.oas3.yaml": is_openapi,
    "*.schema.yaml": is_jsonschema,
    "context-*.ld.yaml": is_framing_context,
}

SKIP_SUFFIXES = (
    ".md",
    ".csv",
    ".png",
    ".xml",
    ".xsd",
    ".html",
    ".gitignore",
    ".git",
    ".example.yaml",
)


def validate_file(f: str):
    f = Path(f).absolute()
    f_size = f.stat().st_size
    if f_size > 4 << 20:
        raise ValueError(f"File too big: {f_size}")

    for file_pattern, is_valid in VALID_SUFFIXES.items():
        if Path(f.name).match(file_pattern):
            print(f"Validating {f}")
            if is_valid(f.read_text()):
                return True
            else:
                raise ValueError(f"Invalid file: {f}")
    raise ValueError(f"Unsupported file {f}")


def list_files(basepath):
    for root, dirs, files in os.walk(basepath):
        for f in files:
            if f.endswith(SKIP_SUFFIXES):
                continue
            if f == "index.ttl":
                continue

            yield Path(os.path.join(root, f))
