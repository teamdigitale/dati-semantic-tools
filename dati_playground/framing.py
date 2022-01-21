import json
import logging
from pathlib import Path
from typing import Dict

import pandas as pd
import yaml
from pyld import jsonld

from .utils import MIME_JSONLD, MIME_TURTLE, is_recent_than, parse_graph, yaml_load
from .validators import is_framing_context

log = logging.getLogger(__name__)


def frame_vocabulary(vpath_ttl: Path, context: Dict) -> Dict:
    """
    Extracts information from a turtle file and places
    them in a json-ld graph.

    @param: vpath_ttl - a text/turtle file
    @param: context - a json-ld framing context
    @returns: a json-ld graph with its own context.
    """

    g = parse_graph(vpath_ttl.as_posix(), format=MIME_TURTLE)
    vocab_jsonld = g.serialize(format=MIME_JSONLD)
    log.warning(f"Serialized to json: {vpath_ttl}")
    vocab = json.loads(vocab_jsonld)
    log.warning(f"Loaded from json: {vpath_ttl}")
    data_projection = jsonld.frame(vocab, frame=context)
    log.warning(f"Projected: {vpath_ttl}.")

    if "@graph" in data_projection:
        p = data_projection["@graph"]

        # Strip unmentioned fields
        p = [{k: v for k, v in e.items() if k in context["@context"]} for e in p]
        return {"@graph": p, "@context": context["@context"]}

    p = [{k: v for k, v in data_projection.items() if k in context["@context"]}]
    return {"@graph": p, "@context": context["@context"]}


def frame_components(frame):
    """
    Returns namespaces and fields from a context.
    This does not process nested contexts.
    """
    context = frame["@context"]
    namespaces = {}
    fields = {}
    index = None
    for k, v in context.items():
        if isinstance(v, str) and v[-1] in "#/":
            p = namespaces
        else:
            p = fields
        p[k] = v
    try:
        index = frame["_meta"]["index"]
        fields[index]
        metadata_context = frame["_meta"].get("_context")
    except (KeyError,):
        index = None
        metadata_context = None
    return namespaces, fields, index, metadata_context


def frame_vocabulary_to_csv(
    vpath: Path, frame_context: Path, dest_dir: Path = Path("."), dump_sqlite=True
):
    """JSON-LD framing is a specification to extract information from
    a json-ld described resource.

    This function extracts information from a given resource
    using a context file.
    """
    context_prefix = "." + frame_context.stem[8:]
    context = yaml_load(frame_context)

    if not is_framing_context(yaml.safe_dump(context)):
        raise ValueError(
            f"Missing required field `key` in framing context: {frame_context}"
        )
    namespaces, fields, index, metadata_context = frame_components(context)

    framed_metadata = frame_vocabulary(vpath, metadata_context)

    try:
        csv_metadata = framed_metadata["@graph"][0]
        version = csv_metadata["version"]
        if "@value" in version:
            version = csv_metadata["version"] = version.get("@value", version)
        log.info(f"Version is now {version}")
        if not isinstance(version, str):
            raise ValueError(f"Bad version {version} for {vpath}")

    except (KeyError, IndexError):
        log.warning(
            f"Invalid metadata context: {metadata_context} resulting in {framed_metadata}"
        )
        raise ValueError(
            f"Metadata context defined in {frame_context} cannot be used to extract meaningful data from RDF file: {vpath}."
        )

    framed_data = frame_vocabulary(vpath, context)

    # Save json-ld version.
    dpath = (dest_dir / vpath).with_suffix(context_prefix + ".yaml")
    if is_recent_than(vpath, dpath):
        dpath.write_text(yaml.safe_dump(framed_data))

    # Generate CSV.
    df = pd.DataFrame(framed_data["@graph"])
    if not index:
        raise ValueError("Missing index.")
    df.set_index([index], inplace=True)
    with dpath.with_suffix(".csv").open("w") as fh:
        # Add embedded-metadata to csv. See https://www.w3.org/TR/tabular-data-model/#embedded-metadata
        fh.write(f"# Serializing {vpath}\n")
        fh.write("# @context: " + json.dumps(context["@context"]) + "\n")
        for k, v in csv_metadata.items():
            if k not in ("url", "title", "version", "description"):
                continue
            fh.write(f"# {k}: {v}\n")
        # Dump actual data.
        df.to_csv(fh)

    datastore = dest_dir / "datastore.db"
    if dump_sqlite:
        df_to_sqlite(
            df,
            datastore,
            name=csv_metadata["url"].split("/")[-1].lower(),
            version=csv_metadata["version"],
            description=csv_metadata["description"],
            url=csv_metadata["url"],
            context=context["@context"],
        )
    # Save json-schema version
    dpath = (dest_dir / vpath).with_suffix(context_prefix + ".oas3.yaml")
    dpath.write_text(yaml.safe_dump(df_to_schema(df), indent=2))

    return framed_data, framed_metadata


def df_to_schema(df) -> Dict:
    """
    Converts a DataFrame to a schema.
    """
    import numpy as np

    def _is_valid(entry):
        try:
            return entry.valid_until == np.nan
        except Exception:
            return True

    items = [
        {"const": e.url, "title": e.label_it} for _, e in df.iterrows() if _is_valid(e)
    ]
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Vocabulary",
            "version": "1.0.0",
            "x-summary": "Vocabulary",
            "contact": {
                "name": "Vocabulary",
                "url": "https://foo.bar",
            },
        },
        "components": {
            "schemas": {
                "MyVocabulary": {
                    "description": "A schema containing all the vocabulary terms.",
                    "oneOf": items,
                }
            }
        },
    }


def df_to_sqlite(
    df,
    dpath: Path,
    name: str,
    version: str,
    title: str = None,
    description: str = None,
    context: Dict = None,
    url: str = None,
):
    from pandas.core.frame import DataFrame
    from sqlalchemy import create_engine

    table_name = f"{name}#{version}"
    dpath.parent.mkdir(exist_ok=True, parents=True)
    datastore_path = "sqlite:///" + dpath.absolute().as_posix()
    log.warning(f"Dumping csv to {datastore_path}")
    engine = create_engine(datastore_path, echo=False)
    df.to_sql(f"{table_name}", con=engine, if_exists="replace")
    log.info(f"Dumping context to meta table {context}")
    DataFrame(
        {
            "name": name,
            "title": title or name,
            "description": description or name,
            "version": version,
            "context": json.dumps(context or {}),
            "url": url,
        },
        index=[0],
    ).to_sql(f"{table_name}#meta", con=engine, if_exists="replace")
