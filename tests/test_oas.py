from pathlib import Path

import pytest
from openapi_resolver.__main__ import main

BASEPATH = Path(__file__).parent / "data"


@pytest.mark.parametrize("oas_yaml", BASEPATH.glob("*.oas3.yaml"))
def test_bundle_oas(oas_yaml):
    dst = oas_yaml.with_suffix(".out.yaml")
    if dst.is_file():
        dst.unlink()
    main(oas_yaml, dst.absolute())
    assert dst.is_file()
