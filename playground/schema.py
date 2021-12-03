import logging
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict

import jsonpath_ng
import requests_cache
from pyld import jsonld
from rdflib import DCAT, DCTERMS, OWL, RDF, RDFS, Graph, Literal, URIRef
from rdflib.namespace import Namespace
from requests import get, head

requests_cache.install_cache("oas3_to_turtle")

log = logging.getLogger(__name__)

NS_ADMSAPT = Namespace("https://www.w3.org/italia/onto/ADMS/")
NS_DCATAPT = Namespace("https://dati.gov.it/onto/dcatapt#")
NS_LICENCES = Namespace("https://w3id.org/italia/controlled-vocabulary/licences/")

NS = (
    ("admsapt", NS_ADMSAPT),
    ("dcatapt", NS_DCATAPT),
    ("dcterms", DCTERMS),
    ("owl", OWL),
    ("rdfs", RDFS),
    ("rdf", RDF),
    ("licences", NS_LICENCES),
    ("dcat", DCAT),
)


class Asset:
    def __init__(self, path: str):
        import git

        repo = git.Repo()

        self.path = Path(path).absolute().relative_to(repo.working_tree_dir)
        self.ndc_config = {
            "schemas": {"path": "./assets/schemas"},
            "ndc_uri": "https://w3id.org/italia/schema/",
            "access_url": (
                "https://github.com/ioggstream/json-semantic-playground"
                "/tree/{publication_branch}/"
            ),
            "download_url": (
                "https://raw.githubusercontent.com/ioggstream/json-semantic-playground"
                "/{publication_branch}/"
            ),
            "publication_branch": "master",
        }

    @property
    def uri(self):
        try:
            return (
                self.ndc_config["ndc_uri"]
                + self.path.relative_to(self.ndc_config["schemas"]["path"]).as_posix()
            )
        except ValueError:
            return self.ndc_config["ndc_uri"] + self.path.as_posix()

    @property
    def download_url(self):
        return (
            self.ndc_config["download_url"].format(
                publication_branch=self.ndc_config["publication_branch"]
            )
            + f"{self.path}"
        )

    @property
    def access_url(self):
        return (
            self.ndc_config["access_url"].format(
                publication_branch=self.ndc_config["publication_branch"]
            )
            + self.path.parent.as_posix()
        )


@lru_cache(maxsize=100)
def get_asset(uri):
    netloc = head(uri, allow_redirects=True, headers={"Accept": "text/html"}).url
    asset = get(netloc, headers={"Accept": "text/turtle"})
    return asset.text


def get_semantic_references_from_oas3(schema: Dict):
    """
    Extract semantic information from an annotated OpenAPI 3
    schema downloading information from .

    :param schema: The schema to extract the information from.
    :return: The Turtle string.
    :rtype: str
    """
    jp_context = jsonpath_ng.parse("$..x-jsonld-context")
    jp_refersTo = jsonpath_ng.parse("$..x-refersTo")
    fields = {
        "$.info.title": DCTERMS.title,
        "$.info.description": DCTERMS.description,
        "$.info.version": OWL.versionInfo,
        "$.info.contact.url": DCTERMS.rightsHolder,
    }
    fields = [(jsonpath_ng.parse(k), v) for k, v in fields.items()]
    ret = {}
    for finder, field in fields:
        needle = finder.find(schema)
        if len(needle) > 0:
            ret[field] = Literal(needle[0].value)

    ret[DCTERMS.accrualPeriodicity] = URIRef(
        "http://publications.europa.eu/resource/authority/frequency/IRREG"
    )

    domains = set()
    ontologies = set()
    g = Graph()
    for asset in jp_refersTo.find(schema):
        g.parse(data=get_asset(asset.value), format="turtle")

        domains = domains.union(
            {uri for _, _, uri in g.triples((None, RDFS.domain, None))}
        )
        ontologies = ontologies.union(
            {uri for _, _, uri in g.triples((None, RDFS.isDefinedBy, None))}
        )

    for ctx in jp_context.find(schema):
        g.parse(
            data=jsonld.normalize(
                {"@context": ctx.value, **{"givenName": "foo"}},
                {"algorithm": "URDNA2015", "format": "application/nquads"},
            )
        )
        domains = domains.union(
            {uri for _, _, uri in g.triples((None, RDFS.domain, None))}
        )
        ontologies = ontologies.union(
            {uri for _, _, uri in g.triples((None, RDFS.isDefinedBy, None))}
        )

    return {"domains": list(domains), "ontologies": list(ontologies), **ret}


def oas3_to_turtle(
    schema_uri: str,
    schema: Dict,
    download_url: str,
    access_url: str = None,
    rightsholder: str = None,
):
    """
    Convert an annotated OpenAPI 3 schema to a Turtle string.

    :param uri: The URI of the schema.
    :param schema: The schema to convert.
    :return: The Turtle string.
    :rtype: str
    """
    distribution_url = URIRef(download_url)
    # dataset_uri = URIRef(os.path.splitext(download_url)[0])
    dataset_uri = URIRef(schema_uri)
    semantic_references = get_semantic_references_from_oas3(schema)
    g = Graph()
    for n in NS:
        g.bind(*n)

    ontologies = semantic_references.pop("ontologies")
    domains = semantic_references.pop("domains")

    for k, v in semantic_references.items():
        g.add((dataset_uri, k, v))
    for o in ontologies:
        g.add((dataset_uri, DCTERMS.conformsTo, o))
    for cls in domains:
        g.add((dataset_uri, NS_ADMSAPT.hasKeyClass, cls))

    if rightsholder:  # Pdataset_urio da ndc-catalog.yaml o publiccode.yaml
        g.add((dataset_uri, DCTERMS.rightsHolder, URIRef(rightsholder)))

    g.add((dataset_uri, RDF.type, NS_DCATAPT.Dataset))
    g.add((dataset_uri, DCTERMS.modified, Literal(date.today().isoformat())))
    g.add((dataset_uri, DCAT.distribution, distribution_url))

    # Generate distribution properties
    [
        g.add(triple)
        for triple in [
            (distribution_url, RDF.type, NS_DCATAPT.Distribution),
            (distribution_url, DCTERMS.license, NS_LICENCES.A21_CCBY40),
            (distribution_url, DCAT.accessURL, URIRef(access_url)),
            # (distribution_url, DCAT.downloadURL, download_url),
            (distribution_url, DCAT.mediaType, Literal("application/json")),
            (
                distribution_url,
                DCTERMS.format,
                URIRef(
                    "http://publications.europa.eu/resource/authority/file-type/JSON"
                ),
            ),
        ]
    ]
    log.warning("Generated distribution: %s", g.serialize(format="turtle"))
    return g
