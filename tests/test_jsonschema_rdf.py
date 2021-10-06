"""
Tests for adding semantic contexts to json-schema.
"""
import logging
from pathlib import Path

import pytest
from rdflib.graph import Graph

from playground.tools import is_valid_jsonschema, jsonschema_to_rdf
from playground.utils import MIME_JSONLD, MIME_TURTLE, yaml_load

log = logging.getLogger(__name__)


BASEPATH = Path(__file__).parent / "data"


@pytest.mark.parametrize("schema_file", BASEPATH.glob("*.schema.yaml"))
def test_valid_schema(schema_file):
    log.warning(schema_file)
    is_valid_jsonschema(schema_file)


@pytest.mark.parametrize("schema_file", BASEPATH.glob("*.schema.yaml"))
def test_schema_to_rdf(schema_file):
    log.warning(schema_file)
    schema = yaml_load(schema_file)
    rdf = jsonschema_to_rdf(schema)
    dpath = schema_file.with_suffix(".out.ttl")
    dpath.write_text(rdf)
    raise NotImplementedError


@pytest.mark.parametrize("schema_file", BASEPATH.glob("*.schema.out.ttl"))
def test_rdf_to_schema(schema_file):
    g = Graph()
    g.parse(schema_file, format=MIME_TURTLE)
    schema_ld = g.serialize(format=MIME_JSONLD)
    assert "@graph" in schema_ld
    raise NotImplementedError
