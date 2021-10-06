from pathlib import Path

from openapi_resolver.__main__ import main


def test_bundle_oas():
    dst = Path("../openapi/openapi-bundled.yaml")
    if dst.is_file():
        dst.unlink()
    main("openapi/openapi.yaml", dst.absolute())
    assert dst.is_file()
