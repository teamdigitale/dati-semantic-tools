"""
validate.py
"""
import json
import logging
import os
from pathlib import Path
from shutil import copy

from dati_playground import validators
from dati_playground.schema import build_schema
from dati_playground.tools import build_semantic_asset, build_vocabularies, yaml_load

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


valid_suffixes = {
    "*.ttl": validators.is_turtle,
    "*.shacl": validators.is_turtle,
    "*.ld.yaml": validators.is_jsonld,
    "*.oas3.yaml": validators.is_openapi,
    "*.schema.yaml": validators.is_jsonschema,
    "context-*.ld.yaml": validators.is_framing_context,
}

skip_suffixes = (
    ".md",
    ".csv",
    ".png",
    ".xml",
    ".xsd",
    ".html",
    ".gitignore",
    ".git",
    ".example.yaml",
)


def validate_file(f: str):
    f = Path(f).absolute()
    f_size = f.stat().st_size
    if f_size > 4 << 20:
        raise ValueError(f"File too big: {f_size}")

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
    dpath.parent.mkdir(parents=True, exist_ok=True)
    data = yaml_load(fpath.as_posix())
    dpath.write_text(json.dumps(data, indent=2))

    copy(fpath, buildpath / fpath.parent / fpath.name)


def list_files(basepath):
    for root, dirs, files in os.walk(basepath):
        for f in files:
            if f.endswith(skip_suffixes):
                continue
            if f == "index.ttl":
                continue

            yield Path(os.path.join(root, f))


import click


@click.command()
@click.option("--validate", default=False)
@click.option("--build-semantic", default=False)
@click.option("--build-json", default=False)
@click.option("--build-schema-index", default=False)
@click.option("--build-csv", default=False)
@click.option("--pattern", default="")
@click.option("--exclude", default=["NoneString"], type=str, multiple=True)
def main(
    validate,
    build_semantic,
    build_json,
    build_csv,
    pattern,
    exclude,
    build_schema_index,
):
    basepath = Path("assets")
    buildpath = Path("_build")
    buildpath.mkdir(exist_ok=True, parents=True)
    from multiprocessing import Pool

    file_list = [
        x
        for x in list(list_files(basepath))
        if (pattern in x.name)
        and all(exclude_item not in x.name for exclude_item in exclude)
    ]

    log.warning(f"Examining {file_list} with {exclude}")
    workers = Pool(processes=4)

    if validate:
        workers.map(validate_file, file_list)

    if build_semantic:
        workers.starmap(
            build_semantic_asset,
            ((f, buildpath) for f in file_list if f.suffix == ".ttl"),
        )
    if build_csv:
        workers.starmap(
            build_vocabularies,
            ((f, buildpath) for f in file_list if f.suffix == ".ttl"),
        )

    if build_json:
        workers.starmap(
            build_yaml_asset, ((f, buildpath) for f in file_list if f.suffix == ".yaml")
        )

    if build_schema_index:
        workers.starmap(
            build_schema,
            ((f, buildpath) for f in file_list if f.name.endswith((".oas3.yaml",))),
        )
        workers.starmap(
            build_schema,
            ((f, Path(".")) for f in file_list if f.name.endswith((".oas3.yaml",))),
        )

    workers.close()


if __name__ == "__main__":
    main()
