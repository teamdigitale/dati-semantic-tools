import json
import logging
import os
from pathlib import Path

import pandas as pd
import pytest
from pyld import jsonld
from rdflib.graph import Graph

from dati_playground.framing import (
    frame_components,
    frame_vocabulary,
    frame_vocabulary_to_csv,
)
from dati_playground.utils import MIME_JSONLD, MIME_TURTLE, yaml_load

BASEPATH = Path(__file__).absolute().parent.parent


def test_frame_vocabulary():
    fpath = BASEPATH / "tests" / "data"
    vpath = fpath / "codelist.ttl"
    cpath = fpath / "codelist.context.ld.yaml"
    context = yaml_load(cpath)
    ret = frame_vocabulary(vpath, context)
    item = ret["@graph"][0]
    assert item
    assert set(item.keys()) < set(context["@context"])


def test_vocabulary_csv():
    fpath = BASEPATH / "tests" / "data"
    vpath = fpath / "codelist.ttl"
    cpath = fpath / "codelist.context.ld.yaml"
    context = yaml_load(cpath)
    vocab_jsonld = frame_vocabulary(vpath, context)
    namespaces, fields, index, metadata_context = frame_components(context)

    df = pd.DataFrame(vocab_jsonld["@graph"])
    if index:
        df.set_index([index], inplace=True)

    csv_path = fpath.with_suffix(".out.csv")
    df.to_csv(csv_path)
    assert (
        "ZR0,http://publications.europa.eu/resource/authority/country/ZR0,true,1960-06-30,ZR0,Zaire,,1997-05-17"
        in csv_path.read_text()
    )


def walk_path(base: Path, pattern: str):
    for root, dir, files in os.walk(base):
        for f in files:
            fpath = Path(root) / f
            if fpath.match(pattern):
                yield fpath


@pytest.mark.parametrize(
    "fpath", walk_path(BASEPATH / "assets" / "vocabularies", "*/latest/curr*.ttl")
)
def test_frame_vocabulary_all(fpath):
    contexts = fpath.parent.glob("context-*.ld.yaml")
    print(fpath)
    dest_dir = Path("out/")
    for context_path in contexts:

        framed_data, framed_metadata = frame_vocabulary_to_csv(
            fpath, context_path, dest_dir
        )
        metadata = framed_metadata["@graph"][0]
        assert metadata["title"]
        assert metadata["description"]
        assert metadata["version"]


def test_context_ns():
    fpath = BASEPATH / "assets" / "vocabularies" / "countries" / "latest"
    cpath = fpath / "context-short.ld.yaml"
    context = yaml_load(cpath)
    namespaces, fields, index, metadata_context = frame_components(context)
    assert index


log = logging.getLogger(__name__)


@pytest.mark.skip(msg="To be done")
def test_frame_big():
    fpath = (
        BASEPATH / "tests" / "data" / "class-sum-leg" / "latest" / "class-sum-leg.ttl"
    )
    context = yaml_load(fpath.parent / "context-short.ld.yaml")
    g = Graph()
    g.parse(fpath.as_posix(), format=MIME_TURTLE)
    vocab_jsonld = g.serialize(format=MIME_JSONLD)
    log.warning("Serialized to json.")
    vocab = json.loads(vocab_jsonld)
    log.warning("Loaded from json.")
    data_projection = jsonld.frame(vocab, frame=context)
    log.warning("Projected.")
    assert data_projection
