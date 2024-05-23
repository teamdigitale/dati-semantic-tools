"""
Tests for adding semantic contexts to json-schema.
"""

import logging
from pathlib import Path

import pytest
import yaml
from pyld import jsonld
from rdflib.graph import Graph

from dati_playground.tools import (
    JSON_SCHEMA_CONTEXT,
    is_valid_jsonschema,
    jsonschema_to_rdf,
)
from dati_playground.utils import MIME_JSONLD, MIME_TURTLE, yaml_load

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

    assert ":properties" in rdf
    assert "given_name" in rdf
    dpath = schema_file.with_suffix(".out.ttl")
    dpath.write_text(rdf)


@pytest.mark.parametrize("schema_file", BASEPATH.glob("*.schema.yaml"))
def test_schema_roundtrip(schema_file):

    schema = yaml_load(schema_file)
    schema_rdf = jsonschema_to_rdf(schema)

    g = Graph()
    g.parse(data=schema_rdf, format=MIME_TURTLE)
    schema_ld = g.serialize(format=MIME_JSONLD)

    schema_js = jsonld.frame(yaml.safe_load(schema_ld), JSON_SCHEMA_CONTEXT)

    # This property is a canary that must be present
    #   in each tested schema.
    assert "given_name" in yaml.dump(schema_js)
