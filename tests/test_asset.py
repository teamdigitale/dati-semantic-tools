import pytest

from dati_playground.asset import Asset
from tests.test_generate_assets import ASSETPATH, walk_path


@pytest.mark.parametrize("fpath", walk_path(ASSETPATH / "schemas", "*.yaml"))
def test_asset_schema(fpath):
    asset = Asset(fpath)
    asset.parse()
    assert asset.serialize("json")
    assert asset.serialize("yaml")


@pytest.mark.parametrize("fpath", walk_path(ASSETPATH / "ontologies", "*.ttl"))
def test_asset_onto(fpath):
    if "-aligns" in fpath.as_posix():
        return
    if "-DBGT" in fpath.as_posix():
        return
    if "example" in fpath.as_posix():
        return
    asset = Asset(fpath)
    asset.parse()
    asset.validate()
    assert asset.serialize("application/ld+json")
    assert asset.serialize("yaml")
