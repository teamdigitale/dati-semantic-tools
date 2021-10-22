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
