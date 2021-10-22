from pathlib import Path

import pandas as pd

from playground.framing import frame_components, frame_vocabulary
from playground.utils import yaml_load

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
    namespaces, fields, index = frame_components(context)

    df = pd.DataFrame(vocab_jsonld["@graph"])
    if index:
        df.set_index([index], inplace=True)

    csv_path = fpath.with_suffix(".out.csv")
    df.to_csv(csv_path)
    assert (
        "ZR0,http://publications.europa.eu/resource/authority/country/ZR0,true,1960-06-30,ZR0,Zaire,,1997-05-17"
        in csv_path.read_text()
    )


import os

import pytest


def walk_path(base: Path, pattern: str):
    for root, dir, files in os.walk(base):
        for f in files:
            fpath = Path(root) / f
            if fpath.match(pattern):
                yield fpath


@pytest.mark.parametrize(
    "fpath", walk_path(BASEPATH / "assets" / "vocabularies", "*l.ttl")
)
def test_frame_vocabulary_all(fpath):
    contexts = fpath.parent.glob("context-*.ld.yaml")
    print(fpath)
    for context in contexts:
        context = yaml_load(context)
        frame_vocabulary(fpath, context)
        namespaces, fields, index = frame_components(context)
    raise NotImplementedError


def test_context_ns():
    fpath = BASEPATH / "assets" / "vocabularies" / "countries" / "latest"
    cpath = fpath / "context.ld.yaml"
    context = yaml_load(cpath)
    namespaces, fields, index = frame_components(context)
    assert not index
