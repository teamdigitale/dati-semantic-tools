import logging
from pathlib import Path

from tests.test_generate_assets import ASSETPATH, walk_path

log = logging.getLogger(__name__)
logging.basicConfig()
import pytest

from dati_playground.asset import Asset


@pytest.mark.parametrize("fpath", walk_path(ASSETPATH / "vocabularies", "*.csv"))
def test_asset_csv(fpath):
    log.error(f"Validating {fpath}")
    asset = Asset(fpath)
    assert asset.type == "csv"
    asset.parse()

    asset.validate()


ontopia = Path(
    "/home/rpolli/workspace-data/daf-ontologie-vocabolari-controllati/VocabolariControllati"
)


@pytest.mark.parametrize("fpath", ontopia.glob("**/*.csv"))
@pytest.mark.skip(reason="Flaky")
def test_asset_csv_ontopia(fpath):
    asset = Asset(fpath, validate_repo=False)
    assert asset.type == "csv"
    asset.parse()

    ret = asset.validate()
    assert ret


@pytest.mark.parametrize("fpath", Path(".").glob("tests/**/education-level.csv"))
def test_asset_datapackage_csv(fpath):
    log.error(f"Validating {fpath}")
    asset = Asset(fpath)
    assert asset.type == "csv"
    asset.parse()

    ret = asset.validate()
    assert ret


@pytest.mark.parametrize("fpath", Path(".").glob("tests/**/ko-education-level.csv"))
def test_asset_datapackage_csv_ko(fpath):
    log.error(f"Validating {fpath}")
    asset = Asset(fpath)
    assert asset.type == "csv"
    asset.parse()
    with pytest.raises(ValueError) as excinfo:
        asset.validate()
    assert "type-error" in str(excinfo.value)


@pytest.mark.parametrize("fpath", Path(".").glob("tests/**/ateco-2007.csv"))
def test_ateco_datapackage_csv(fpath):
    log.error(f"Validating {fpath}")
    asset = Asset(fpath)
    assert asset.type == "csv"
    asset.parse()

    ret = asset.validate()
    assert ret
