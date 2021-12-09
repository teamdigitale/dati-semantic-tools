import json
import logging
from pathlib import Path
from shutil import copy
from typing import Dict

import jsonschema
from pyld import jsonld
from rdflib import Graph

from .framing import frame_vocabulary_to_csv
from .utils import MIME_JSONLD, MIME_TURTLE, is_recent_than, parse_graph, yaml_load

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

    # Use jsonld.compact to simplify the RDF output
    #   retaining all properties and increase readability.
    schema_jsonld = jsonld.compact(schema, ctx=JSON_SCHEMA_CONTEXT)
    g = Graph()
    g.parse(data=json.dumps(schema_jsonld), format=MIME_JSONLD)
    return g.serialize(format=format)


def is_valid_jsonschema(f: Path):
    schema = yaml_load(f)
    jsonschema.Draft7Validator.check_schema(schema)
    log.info(f"Valid json-schema in {f.absolute().as_posix()}")


def build_semantic_asset(asset_path: Path, dest_dir: Path = Path(".")):
    log.warning(f"Building {asset_path} in {dest_dir}")

    if "out" in asset_path.suffixes:
        return

    g = parse_graph(asset_path.as_posix())

    for fmt, ext in [("xml", ".rdf"), (MIME_JSONLD, ".jsonld"), ("ntriples", ".nt")]:
        dpath = (dest_dir / asset_path).with_suffix(ext)
        dpath.parent.mkdir(exist_ok=True, parents=True)
        if not is_recent_than(asset_path, dpath):
            continue
        g.serialize(format=fmt, destination=dpath.as_posix())


def build_vocabularies(asset_path: Path, dest_dir: Path = Path(".")):
    log.warning(f"Building CSV dataset from {asset_path} in {dest_dir}")

    for frame_context in asset_path.parent.glob("context-*.ld.yaml"):
        frame_vocabulary_to_csv(asset_path, frame_context, dest_dir)


def build_yaml_asset(fpath: Path, buildpath: Path = Path(".")):
    if fpath.suffix != ".yaml":
        raise ValueError(f"Not a yaml file: {fpath}")

    log.info(f"Building yaml asset for: {fpath}")
    dsuffix = ".json"
    dpath_name = fpath.name
    if fpath.name.endswith(".ld.yaml"):
        dsuffix = ".jsonld"
        dpath_name = fpath.with_suffix("").name
    dpath = (buildpath / fpath.parent / dpath_name).with_suffix(dsuffix)
    dpath.parent.mkdir(parents=True, exist_ok=True)
    data = yaml_load(fpath.as_posix())
    dpath.write_text(json.dumps(data, indent=2))

    copy(fpath, buildpath / fpath.parent / fpath.name)
