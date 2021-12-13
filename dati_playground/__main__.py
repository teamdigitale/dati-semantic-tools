"""
Validation script for semantic assets.
"""
import logging
from multiprocessing import Pool
from pathlib import Path

from dati_playground import precommit_validators
from dati_playground.schema import build_schema
from dati_playground.tools import (
    build_semantic_asset,
    build_vocabularies,
    build_yaml_asset,
)
from dati_playground.validators import (
    is_jsonschema,
    is_openapi,
    is_turtle,
    list_files,
    validate_file,
)

logging.basicConfig(level=(logging.DEBUG))
log = logging.getLogger(__name__)
import click


@click.command()
@click.argument("command", type=(click.Choice(["validate", "build"])))
@click.argument("files", type=click.Path(exists=True), nargs=(-1))
@click.option("--validate", default=False)
@click.option("--build-semantic", default=False)
@click.option("--build-json", default=False)
@click.option("--build-schema-index", default=False)
@click.option("--build-csv", default=False)
@click.option("--validate-shacl", default=False)
@click.option("--validate-oas3", default=False)
@click.option("--validate-jsonschema", default=False)
@click.option("--validate-versioned-directory", default=False)
@click.option("--validate-turtle", default=False)
@click.option("--pattern", default="")
@click.option("--exclude", default=["NoneString"], type=str, multiple=True)
def main(
    command,
    files,
    validate,
    build_semantic,
    build_json,
    build_csv,
    validate_shacl,
    validate_oas3,
    validate_jsonschema,
    validate_versioned_directory,
    validate_turtle,
    pattern,
    exclude,
    build_schema_index,
):
    if command == "build":

        basepath = Path("assets") if not files else Path(files[0])
        buildpath = Path("_build") if len(files) < 2 else Path(files[1])
        buildpath.mkdir(exist_ok=True, parents=True)

        file_list = [
            x
            for x in list(list_files(basepath))
            if pattern in x.name
            if all((exclude_item not in x.name for exclude_item in exclude))
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
                build_yaml_asset,
                ((f, buildpath) for f in file_list if f.suffix == ".yaml"),
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
        exit(0)
    else:
        errors = []
        if command == "validate":
            for f in files:
                f = Path(f)
                if validate_shacl:
                    precommit_validators.validate_shacl(f)
                if validate_oas3:
                    is_openapi(f.read_text())
                if validate_jsonschema:
                    is_jsonschema(f.read_text())
                if validate_versioned_directory:
                    precommit_validators.validate_directory(f, errors)
                if validate_turtle:
                    is_turtle(f.read_text())
            if errors:
                raise ValueError("Errors found: " + "\n".join(errors))

        else:
            pass
        print("No errors found")


if __name__ == "__main__":
    main()
# okay decompiling __main__.cpython-38.pyc
