import json
import logging
from pathlib import Path
from typing import Dict

import jsonschema
from pyld import jsonld
from rdflib import Graph

from .framing import generate_frame
from .utils import MIME_JSONLD, MIME_TURTLE, yaml_load

log = logging.getLogger(__name__)

JSON_SCHEMA_CONTEXT = yaml_load(
    (Path(__file__).parent / "data" / "json-schema-rdf-context.ld.yaml").absolute()
)


def jsonschema_to_rdf(schema: Dict, format=MIME_TURTLE):
    """Convert a jsonschema to RDF (turtle mime-type)
       using the @context defined in https://www.w3.org/2019/wot/json-schema.
    """
    jsonschema.Draft7Validator.check_schema(schema)

    if "@context" in schema:
        raise NotImplementedError("Multiple contexts are not supported")
    schema = dict(schema, **JSON_SCHEMA_CONTEXT)
    schema_jsonld = jsonld.flatten(schema)
    g = Graph()
    g.parse(data=json.dumps(schema_jsonld), format=MIME_JSONLD)
    return g.serialize(format=format)


def is_valid_jsonschema(f: Path):
    schema = yaml_load(f)
    jsonschema.Draft7Validator.check_schema(schema)
    log.info(f"Valid json-schema in {f.absolute().as_posix()}")


def generate_asset(asset_path_ttl: Path):
    """Generate rdf, nt and jsonld files from a ttl files.
    """
    for f in asset_path_ttl.glob("*/*/*.ttl"):
        if "out.ttl" in f.as_posix():
            continue
        g = Graph()
        g.parse(f.as_posix())

        for fmt, ext in [
            ("xml", ".out.rdf"),
            (MIME_JSONLD, ".out.jsonld"),
            ("ntriples", ".out.nt"),
        ]:
            dpath = f.with_suffix(ext).as_posix()
            g.serialize(format=fmt, destination=dpath)

        generate_frame(f)
