import json
from pathlib import Path

import yaml
from rdflib import Graph

from playground.tools import generate_asset, jsonschema_to_rdf
from playground.utils import MIME_JSONLD, yaml_load, yaml_to_json

SCHEMA_CERTIFICATE = yaml.safe_load(Path("schemas/certificato.yaml").read_text())
BASEPATH = Path(__file__).absolute().parent / "data"


def test_generate_assets():
    """
    Generate assets from a turtle source.
    """

    g = Graph()
    g.parse(BASEPATH / "data.ttl")
    g.serialize(format="xml", destination="data.rdf.out")
    g.serialize(format="application/ld+json", destination="data.jsonld.out")
    g.serialize(format="ntriples", destination="data.nt.out")


def test_generate_ontologies():
    basepath = BASEPATH.parent
    generate_asset(basepath / "ontologies")


def test_generate_vocabularies():
    basepath = BASEPATH.parent
    generate_asset(basepath / "vocabularies")


def test_context_to_rdf():
    basepath = BASEPATH.parent
    asset_path = basepath / "schemas"
    for f in asset_path.glob("*/*/*.ld.yaml"):
        g = Graph()
        data = yaml_to_json(f.read_text())
        g.parse(data=data, format="application/json+ld")

        for fmt, ext in [
            ("xml", ".out.rdf"),
            (MIME_JSONLD, ".out.jsonld"),
            ("ntriples", ".out.nt"),
            ("turtle", ".out.ttl"),
        ]:
            dpath = f.with_suffix(ext).as_posix()
            g.serialize(format=fmt, destination=dpath)


def test_generate_json():
    schema_path = BASEPATH.parent / "schemas"

    for f in schema_path.glob("*/*/*.yaml"):
        dsuffix = ".jsonld" if f.as_posix().endswith(".ld.yaml") else ".json"
        dpath = f.with_suffix(dsuffix)
        data = yaml_load(f)
        dpath.write_text(json.dumps(data, indent=2))


def test_create_schemas_json():
    schemas_path = Path("schemas/")

    for f in schemas_path.glob("*/*/*.yaml"):
        if not f.is_file():
            continue

        fpath = f.absolute().as_posix()
        data = f.read_text()

        if fpath.endswith(".ld.yaml"):
            dpath = fpath.replace(".ld.yaml", ".jsonld")
            Path(dpath).write_text(yaml_to_json(data))
            continue

        if fpath.endswith(".oas3.yaml"):
            dpath = fpath.replace(".oas3.yaml", ".oas3.json")
            Path(dpath).write_text(yaml_to_json(data))
            continue

        if fpath.endswith(".schema.yaml"):
            dpath = fpath.replace(".schema.yaml", ".schema.json")
            Path(dpath).write_text(yaml_to_json(data))

            dpath = fpath.replace(".schema.yaml", ".schema.ttl")
            Path(dpath).write_text(jsonschema_to_rdf(yaml.safe_load(data)))
            continue
