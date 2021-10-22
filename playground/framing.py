from pathlib import Path
from typing import Dict

import pandas as pd
import yaml
from pyld import jsonld
from rdflib import Graph

from .utils import MIME_JSONLD, MIME_TURTLE, yaml_load
from .validators import is_framing_context


def frame_vocabulary(vpath_ttl: Path, context: Dict) -> Dict:
    """
    Extracts information from a turtle file and places
    them in a json-ld graph.

    @param: vpath_ttl - a text/turtle file
    @param: context - a json-ld framing context
    @returns: a json-ld graph with its own context.
    """
    g = Graph()
    vocab = g.parse(vpath_ttl.as_posix(), format=MIME_TURTLE)
    vocab = yaml.safe_load(g.serialize(format=MIME_JSONLD))
    projection = jsonld.frame(vocab, frame=context)
    p = projection["@graph"]

    # Strip unmentioned fields
    p = [{k: v for k, v in e.items() if k in context["@context"]} for e in p]
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
    except (KeyError,):
        index = None
    return namespaces, fields, index


def generate_frame(vpath: Path, dest_dir: Path = Path(".")):
    """JSON-LD framing is a specification to extract information from
    a json-ld described resource.

    This function extracts information from a given resource
    using a set of context files.
    """

    for frame_context in vpath.parent.glob("context-*.ld.yaml"):
        context_prefix = "." + frame_context.stem[8:]
        context = yaml_load(frame_context)

        if not is_framing_context(yaml.safe_dump(context)):
            raise ValueError(
                f"Missing required field `key` in framing context: {frame_context}"
            )
        namespaces, fields, index = frame_components(context)

        framed_data = frame_vocabulary(vpath, context)
        dpath = (dest_dir / vpath).with_suffix(context_prefix + ".yaml")
        dpath.write_text(yaml.dump(framed_data))

        df = pd.DataFrame(framed_data["@graph"])
        if not index:
            raise ValueError("Missing index.")
        df.set_index([index], inplace=True)
        df.to_csv(dpath.with_suffix(".csv").as_posix())
