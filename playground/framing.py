import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict

import pandas as pd
import yaml
from pandas.core.frame import DataFrame
from pyld import jsonld
from rdflib import Graph

from .utils import MIME_JSONLD, MIME_TURTLE, yaml_load
from .validators import is_framing_context

log = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def parse_graph(vpath_ttl, format):
    log.warning(f"Parsing file: {vpath_ttl}")
    g = Graph()
    g.parse(vpath_ttl, format=MIME_TURTLE)
    return g


def frame_vocabulary(vpath_ttl: Path, context: Dict) -> Dict:
    """
    Extracts information from a turtle file and places
    them in a json-ld graph.

    @param: vpath_ttl - a text/turtle file
    @param: context - a json-ld framing context
    @returns: a json-ld graph with its own context.
    """
    # g = Graph()
    # vocab = g.parse(vpath_ttl.as_posix(), format=MIME_TURTLE)
    g = parse_graph(vpath_ttl.as_posix(), format=MIME_TURTLE)
    vocab = yaml.safe_load(g.serialize(format=MIME_JSONLD))
    data_projection = jsonld.frame(vocab, frame=context)

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
    dpath.write_text(yaml.dump(framed_data))

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

    if dump_sqlite:
        datastore = dest_dir / "datastore.db"
        df_to_sqlite(
            df,
            datastore,
            name=csv_metadata["url"].split("/")[-1].lower(),
            version=csv_metadata["version"],
            description=csv_metadata["description"],
            url=csv_metadata["url"],
            context=context["@context"],
        )
    return framed_data, framed_metadata


def df_to_sqlite(
    df: DataFrame,
    dpath: Path,
    name: str,
    version: str,
    title: str = None,
    description: str = None,
    context: Dict = None,
    url: str = None,
):
    from sqlalchemy import create_engine

    table_name = f"{name}#{version}"

    datastore_path = "sqlite:///" + dpath.absolute().as_posix()
    engine = create_engine(datastore_path, echo=False)
    df.to_sql(f"{table_name}", con=engine, if_exists="replace")
    DataFrame(
        {
            "name": name,
            "title": title or name,
            "description": description or name,
            "version": version,
            "context": context or {},
            "url": url,
        },
        index=[0],
    ).to_sql(f"{table_name}#meta", con=engine, if_exists="replace")
