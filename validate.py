"""
validate.py
"""
import json
import logging
import os
from pathlib import Path

from playground import validators
from playground.tools import build_asset, yaml_load

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


valid_suffixes = {
    "*.ttl": validators.is_turtle,
    "*.ld.yaml": validators.is_jsonld,
    "*.oas3.yaml": validators.is_openapi,
    "*.schema.yaml": validators.is_jsonschema,
    "context-*.ld.yaml": validators.is_framing_context,
}

skip_suffixes = (".md", ".csv", ".png", ".xml", ".xsd")


def validate_file(f: str):
    f = Path(f).absolute()

    if f.stat().st_size > 1 << 20:
        raise ValueError(f"File too big: {f.size}")

    for file_pattern, is_valid in valid_suffixes.items():
        if Path(f.name).match(file_pattern):
            print(f"Validating {f}")
            if is_valid(f.read_text()):
                return True
            else:
                raise ValueError(f"Invalid file: {f}")
    raise ValueError(f"Unsupported file {f}")


def build_yaml_asset(fpath: Path, buildpath: Path = Path(".")):
    if fpath.suffix != ".yaml":
        raise ValueError(f"Not a yaml file: {fpath}")

    log.info(f"Building yaml asset for: {fpath}")
    dsuffix = ".json"
    dpath_name = fpath.name
    if fpath.name.endswith(".ld.yaml"):
        dsuffix = ".jsonld"
        dpath_name = fpath.with_suffix("").name
    dpath = (buildpath / fpath.parent / dpath_name).with_suffix(dsuffix)
    data = yaml_load(fpath.as_posix())
    dpath.write_text(json.dumps(data, indent=2))


def list_files(basepath):
    for root, dirs, files in os.walk(basepath):
        for f in files:
            if f.endswith(skip_suffixes):
                continue
            if f == "index.ttl":
                continue

            yield Path(os.path.join(root, f))


if __name__ == "__main__":
    basepath = Path("assets")
    buildpath = Path("_build")

    from multiprocessing import Pool

    file_list = list(list_files(basepath))
    workers = Pool(processes=4)

    workers.map(validate_file, file_list)
    workers.starmap(
        build_asset, ((f, buildpath) for f in file_list if f.suffix == ".ttl")
    )
    # workers.starmap(build_yaml_asset, ((f, buildpath) for f in file_list if f.suffix == ".yaml"))

    workers.close()
