import logging
from pathlib import Path
from typing import List

from rdflib import OWL, RDF, SKOS, Graph, Namespace

log = logging.getLogger(__name__)


def extract_main_uri(ttl_fpath: Path):
    """
    Extracts the main URI relative to the specified TTL file.

    Args:
        ttl_fpath (Path): The path of the TTL file.

    Returns:
        str: The main relative URI if found, otherwise None.
    """
    try:
        g = Graph()
        g.parse(str(ttl_fpath), format="ttl")
    except Exception as e:
        # errors.append(f"{fpath} is not a valid Turtle file: {e}")
        raise Exception(e)

    # Define namespace prefixes
    dcatapit = Namespace("http://dati.gov.it/onto/dcatapit#")

    main_uri = None

    for s, p, o in g:
        if (s, RDF.type, OWL.Ontology) in g and "onto" in str(
            ttl_fpath.parents[1]
        ).lower():
            main_uri = s
            break
        elif p == RDF.type and o == dcatapit.Dataset:
            main_uri = s
            break
        # elif (s, RDF.type, RDFS.Class) in g:
        #     main_uri = s
        #     break
        elif (s, RDF.type, SKOS.ConceptScheme) in g:
            main_uri = s
            break

    return main_uri


def validate(fpath: Path, errors: List[str]):

    log.debug(f"File Path:{fpath}")
    suffix = fpath.suffix

    if suffix != ".ttl":
        return True

    # Extract uri from file path
    try:
        uri = extract_main_uri(fpath)
        log.debug(f"URI: {uri}")
    except Exception as e:
        errors.append(
            f"It's not possible to extract URI from {fpath}, it is not a valid Turtle file: {e}"
        )
        return False

    if uri:
        # Extract the final part of the URI
        uri_parts = str(uri).split("/")
        last_uri_part = uri_parts[-1]
        if last_uri_part == "":
            last_uri_part = uri_parts[-2]

        # Check if the parent of the fpath contain "schema"
        if "schema" in fpath.parts[1].lower():

            # Check if the file with .oas3.yaml extension exists in the same directory
            yaml_file = Path(fpath.parent, f"{last_uri_part}")

            if not yaml_file.exists():
                log.debug(
                    f"The file '{yaml_file}' corresponding to its relative URI '{uri}' does not exist."
                )
                errors.append(
                    f"The file '{yaml_file}' corresponding to its relative URI '{uri}' does not exist."
                )
                return False
        else:
            if fpath.stem != last_uri_part:
                log.debug(f"The file '{fpath}' does not match its relative URI '{uri}'")
                errors.append(
                    f"The file '{fpath}' does not match its relative URI '{uri}'"
                )
                return False
    return True
