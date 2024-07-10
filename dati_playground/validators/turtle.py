import logging
from pathlib import Path

from rdflib import Graph
from rdflib.plugins.parsers.notation3 import BadSyntax

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

from dati_playground.utils import MIME_TURTLE


def validate(fpath: Path, errors: list):
    try:
        content = fpath.read_text(encoding="utf-8")
        g = Graph()
        g.parse(data=content, format=MIME_TURTLE)
        return True
    except (BadSyntax, Exception) as e:
        errors.append(f"{fpath} is not a valid Turtle file: {e}")
        return False
