from pathlib import Path

import pytest
import yaml
from openapi_resolver.__main__ import main
from rdflib import DCAT, DCTERMS, OWL, RDFS
from rdflib.namespace import Namespace
from rdflib.term import URIRef

from dati_playground.schema import (
    NS_CPV,
    Asset,
    build_schema,
    get_schema_assets,
    oas3_to_turtle,
)

BASEPATH = Path(__file__).parent / "data"


@pytest.mark.parametrize("oas_yaml", BASEPATH.glob("*.oas3.yaml"))
def test_bundle_oas(oas_yaml):
    dst = oas_yaml.with_suffix(".out.yaml")
    if dst.is_file():
        dst.unlink()
    main(oas_yaml, dst.absolute())
    assert dst.is_file()


@pytest.fixture
def harvest_config():
    return {
        "schemas": {"path": "./assets/schemas"},
        "ipa_code": ("pcm"),
        "access_url": (
            "https://github.com/ioggstream/json-semantic-playground"
            "/tree/{publication_branch}/"
        ),
        "download_url": (
            "https://raw.githubusercontent.com/ioggstream/json-semantic-playground"
            "/{publication_branch}/"
        ),
        "publication_branch": "master",
    }


def test_schema_url(harvest_config):
    schema_yaml = Path("./assets/schemas/person/v202108.01/person.oas3.yaml")
    asset = Asset(schema_yaml)

    assert (
        asset.access_url
        == "https://github.com/ioggstream/json-semantic-playground/tree/master/assets/schemas/person/v202108.01"
    )
    assert (
        asset.download_url
        == "https://raw.githubusercontent.com/ioggstream/json-semantic-playground/master/assets/schemas/person/v202108.01/person.oas3.yaml"
    )

    assert (
        asset.uri == "https://w3id.org/italia/schema/person/v202108.01/person.oas3.yaml"
    )


@pytest.mark.parametrize("oas_yaml", BASEPATH.glob("schema.oas3.yaml"))
def test_turtlize_oas(oas_yaml, harvest_config):
    oas_schema = yaml.safe_load(oas_yaml.read_text())

    asset = Asset(oas_yaml)

    g = oas3_to_turtle(
        asset.uri,
        oas_schema,
        access_url=asset.access_url,
        download_url=asset.download_url,
    )

    mandatory_properties = [
        DCTERMS.title,
        DCTERMS.description,
        DCTERMS.rightsHolder,
        DCTERMS.accrualPeriodicity,
        DCTERMS.modified,
        #        DCTERMS.theme,
        OWL.versionInfo,
        DCAT.distribution,
    ]
    assert set(mandatory_properties) < set(g.predicates())
    assert URIRef("https://w3id.org/italia/onto/CPV") in g.objects()
    assert URIRef("https://w3id.org/italia/onto/CPV/Person") in g.objects()


@pytest.mark.parametrize(
    "oas_yaml", (BASEPATH.parent.parent / "assets").glob("**/*.oas3.yaml")
)
def test_build_schema(oas_yaml, harvest_config):
    build_schema(oas_yaml, Path("/tmp"))


def test_get_schema_assets():
    NS_Indicator = Namespace("https://w3id.org/italia/onto/Indicator/")
    assets = get_schema_assets(
        {
            "@vocab": "https://w3id.org/italia/onto/CPV/",
            "indicator": "https://w3id.org/italia/onto/Indicator/",
            "loc": "https://w3id.org/italia/onto/CLV/",
            "given_name": "givenName",
            "tax_code": "taxCode",
            "ts": "indicator:computedAtTime",
            "country": "clv:lat",
        }
    )
    assert {a for _, _, a in assets.triples((None, RDFS.domain, NS_CPV.Person))}
    assert {
        a
        for _, _, a in assets.triples(
            (None, RDFS.domain, NS_Indicator.IndicatorCalculation)
        )
    }
