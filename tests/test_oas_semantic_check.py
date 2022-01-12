from pathlib import Path

import pytest

from dati_playground.schema import ndc_semantic_bundle, validate_context
from dati_playground.utils import yaml_load

BASEPATH = Path(__file__).parent / "data"

import yaml


@pytest.mark.parametrize(
    "oas30_yaml", (BASEPATH.parent.parent / "assets").glob("**/*.oas3.yaml")
)
def test_api_validation(oas30_yaml):
    spec = yaml_load(oas30_yaml)
    ret = ndc_semantic_bundle(spec)
    assert ret
    print(yaml.safe_dump(ret))
    # raise NotImplementedError


def test_asset_info_base():
    context = {
        "@vocab": "https://w3id.org/italia/onto/CPV/",
        "family_name": "familyName",
    }
    ret = validate_context(context)
    assert (
        set(
            {
                "onto": "https://w3id.org/italia/onto/CPV",
                "domain": "https://w3id.org/italia/onto/CPV/Person",
            }
        )
        < set(ret["https://w3id.org/italia/onto/CPV/familyName"])
    )


def test_asset_info_fail():
    context = {
        "@vocab": "https://w3id.org/italia/onto/CPV/",
        "family_name": "MISSING",
        "given_name": "givenName",
    }
    with pytest.raises(ValueError):
        ret = validate_context(context)
        assert (
            set(
                {
                    "onto": "https://w3id.org/italia/onto/CPV",
                    "domain": "https://w3id.org/italia/onto/CPV/Person",
                }
            )
            < set(ret["https://w3id.org/italia/onto/CPV/familyName"])
        )


def test_asset_info_advanced():
    context = {
        "@vocab": "https://w3id.org/italia/onto/CPV/",
        "family_name": "familyName",
        "town": "https://w3id.org/italia/onto/CLV/City",
    }
    ret = validate_context(context)
    assert (
        set(
            {
                "onto": "https://w3id.org/italia/onto/CPV",
                "domain": "https://w3id.org/italia/onto/CPV/Person",
            }
        )
        < set(ret["https://w3id.org/italia/onto/CPV/familyName"])
    )
    assert (
        set(
            {
                "onto": "https://w3id.org/italia/onto/CLV",
                "domain": "https://w3id.org/italia/onto/CLV/City",
            }
        )
        < set(ret["https://w3id.org/italia/onto/CLV/City"])
    )
