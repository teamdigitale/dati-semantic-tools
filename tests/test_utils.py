from pathlib import Path

from rdflib import URIRef

from dati_playground.utils import load_all_assets


def test_load_all_assets():
    g = load_all_assets(Path(__file__).parent.parent / "assets" / "ontologies")
    assert list(
        g.triples((URIRef("https://w3id.org/italia/onto/CPV/Person"), None, None))
    )
