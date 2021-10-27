import logging
import os
from pathlib import Path

import pytest
import yaml
from rdflib import Graph

from playground.tools import build_semantic_asset, build_vocabularies, jsonschema_to_rdf
from playground.utils import MIME_JSONLD, yaml_to_json
from validate import build_yaml_asset

ASSETPATH = Path(__file__).absolute().parent.parent / "assets"
BASEPATH = Path(__file__).absolute().parent / "data"
testout = BASEPATH / "out"


log = logging.getLogger(__name__)


def test_generate_assets():
    """
    Generate assets from a turtle source.
    """

    g = Graph()
    g.parse(BASEPATH / "data.ttl")
    g.serialize(format="xml", destination="data.rdf.out")
    g.serialize(format="application/ld+json", destination="data.jsonld.out")
    g.serialize(format="ntriples", destination="data.nt.out")


def walk_path(base: Path, pattern: str):
    for root, dir, files in os.walk(base):
        for f in files:
            fpath = Path(root) / f
            if fpath.match(pattern):
                yield fpath


@pytest.mark.parametrize("fpath", walk_path(ASSETPATH / "ontologies", "*.ttl"))
def test_generate_ontologies(fpath):
    log.warning(fpath)
    build_semantic_asset(fpath, dest_dir=testout)


@pytest.mark.parametrize(
    "fpath", walk_path(ASSETPATH / "vocabularies", "latest/count*.ttl")
)
def test_generate_vocabularies(fpath):
    build_vocabularies(fpath, dest_dir=testout)
    assert fpath.parent.glob("*.csv")


@pytest.mark.parametrize("fpath", walk_path(ASSETPATH / "schemas", "*.yaml"))
def test_generate_json(fpath):
    build_yaml_asset(fpath, dest_dir=testout)


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
