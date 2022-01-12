from pathlib import Path

import jsonpath_ng
import jsonschema
import pytest

from dati_playground.utils import yaml_load

BASEPATH = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    "oas30_yaml", (BASEPATH.parent.parent / "assets").glob("**/*.oas3.yaml")
)
def test_get_context(oas30_yaml):
    total_count = 0
    semantic_count = 0
    spec = yaml_load(oas30_yaml)
    for schema_fragment, schema_content, context in get_context_info(spec):
        if schema_content.get("type") != "object":
            # const, oneOf, anyOf, allOf are not supported.
            # string, number, integer, boolean, null, array, object are supported.
            raise NotImplementedError

        properties = schema_content.get("properties", {})
        for property_name, property_schema in properties.items():
            if property_schema.get("type") in ("object", "array"):
                # only basic types are supported.
                pass  # raise NotImplementedError
            total_count += 1
            semantic_count += bool(context.get(property_name))

        print(schema_fragment, total_count, semantic_count)
    # raise NotImplementedError


from typing import Dict


def get_context_info(spec: Dict):
    jp_context = jsonpath_ng.parse("$..x-jsonld-context")
    for ctx in jp_context.find(spec):
        context = ctx.value
        schema_fragment = get_context_jsonpointer(ctx)
        schema_content = ctx.context.value

        # Validate the schema. It throws in case of exceptions.
        assert jsonschema.Draft7Validator.check_schema(schema_content) is None

        yield schema_fragment, schema_content, context


def get_context_jsonpointer(ctx):
    return "#/" + "/".join(dump(ctx.full_path.left))


def dump(full_path):
    if hasattr(full_path, "left"):
        yield from dump(full_path.left)
    if hasattr(full_path, "right"):
        yield from dump(full_path.right)
    else:
        yield full_path.fields[0]
