from pathlib import Path
from urllib.parse import urlencode

import requests
from jsonpath_ng import parse
from rdflib import Graph

from playground.utils import yaml_load

SCHEMA_CERTIFICATE = yaml_load("schemas/certificato.yaml")
BASEPATH = Path(__file__).absolute().parent.parent


def test_query_rdf():
    g = Graph()
    ret = g.query(
        """
PREFIX l0: <https://w3id.org/italia/onto/l0/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT * WHERE {


?class rdfs:isDefinedBy ?onto;
   a owl:Class

. ?class rdfs:isDefinedBy <https://w3id.org/italia/onto/CPV>

. ?property rdfs:domain ?class

. OPTIONAL { ?property l0:controlledVocabulary ?range } .


} LIMIT 20
    """
    )
    for row in ret:
        print(row)
    raise NotImplementedError


def sparql_get(id_):
    sparql_endpoint = "http://localhost:8890/sparql/"
    qp = {
        "query": [
            f"""
PREFIX l0: <https://w3id.org/italia/onto/l0/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
prefix admsapit: <https://w3id.org/italia/onto/ADMS/>

SELECT DISTINCT ?subject, ?subject_type, ?domain, ?ontology_version, ?last_version, ?last_modified WHERE {{


VALUES ?subject {{ <{id_}> }}

. ?subject rdfs:isDefinedBy ?domain ;
    owl:versionInfo  ?ontology_version ;
    rdf:type ?subject_type

. ?domain dct:modified ?last_modified

. OPTIONAL {{ ?domain admsapit:last ?last_version }}
. OPTIONAL {{ ?subject rdfs:domain ?domain }}

}} LIMIT 1
"""
        ],
        "format": ["application/sparql-results+json"],
        "timeout": ["0"],
        "debug": ["on"],
        "run": [" Run Query "],
    }

    ep = urlencode(qp, doseq=True)
    data = requests.get(f"{sparql_endpoint}?" + ep)
    return data.json()


def test_find_semantics():
    """
    Returns a list of semantics objects
    referenced by the original document.
    """
    jsonpath_expr = parse("*..x-refersTo")
    references = {}
    query_fields = [
        "subject",
        "subject_type",
        "domain",
        "ontology_version",
        "last_version",
        "last_modified",
    ]
    found, total = 0, 0
    for entry in jsonpath_expr.find(SCHEMA_CERTIFICATE):
        total += 1
        ndc = sparql_get(entry.value)["results"]["bindings"]
        if not len(ndc):
            continue
        found += 1

        ndc = ndc[0]
        references[entry.value] = dict(
            referrer="/".join(entry.context.path.fields),
            **{x: ndc[x]["value"] for x in query_fields},
        )
    references["coverage"] = found / total

    raise NotImplementedError


def test_parse_schema():
    jsonpath_expr = parse("*..x-refersTo")
    ret = []
    context = {}
    for entry in jsonpath_expr.find(SCHEMA_CERTIFICATE):
        entry.context.full_path
        v = {
            "value": entry.value,
            "path": "/".join(entry.context.path.fields),
            "type": entry.context.value.get("type"),
        }
        if entry.context.value.get("type") == "object":
            context["@type"] = entry.value
        context[v["path"]] = v["value"]

        ndc_data = sparql_get(entry.value)["results"]["bindings"][0]
        v["version"] = ndc_data["v"]["value"]
        v["domain"] = ndc_data.get("domain", {}).get("value", None)
        ret.append(v)
    raise NotImplementedError
