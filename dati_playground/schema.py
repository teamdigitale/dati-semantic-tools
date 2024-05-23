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
from requests import get

from .utils import is_recent_than, load_all_assets, yaml_load

requests_cache.install_cache("oas3_to_turtle")

log = logging.getLogger(__name__)

NS_ADMSAPT = Namespace("https://www.w3.org/italia/onto/ADMS/")
NS_DCATAPIT = Namespace("http://dati.gov.it/onto/dcatapit#")
NS_LICENCES = Namespace("https://w3id.org/italia/controlled-vocabulary/licences/")
NS_ITALIA = Namespace("https://w3id.org/italia/")
NS_CPV = Namespace("https://w3id.org/italia/onto/CPV/")
NS_FOAF = Namespace("http://xmlns.com/foaf/0.1/")
NS = (
    ("admsapt", NS_ADMSAPT),
    ("dcatapit", NS_DCATAPIT),
    ("dct", DCTERMS),
    ("owl", OWL),
    ("rdfs", RDFS),
    ("rdf", RDF),
    ("licences", NS_LICENCES),
    ("dcat", DCAT),
    ("it", NS_ITALIA),
    ("cpv", NS_CPV),
    ("foaf", NS_FOAF),
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
    log.debug(f"Loading asset for <{uri}>.")

    # import pdb; pdb.set_trace()
    g = Graph()
    tstore = load_all_assets(Path("assets/ontologies"))
    g += tstore.triples((URIRef(uri), None, None))
    if next(g.subjects(), None):
        log.debug(f"Returning graph: {g.serialize()}")
        return g

    log.info("Loading stuff from ontopia.")
    netloc = uri.replace(
        "https://w3id.org/italia/", "https://ontopia-lodview.agid.gov.it/"
    )
    asset = get(netloc, headers={"Accept": "text/turtle"}, timeout=10)
    g.parse(data=asset.text, format="text/turtle")
    return g


def get_semantic_references_from_oas3(schema: Dict):
    """
    Extract semantic information from an annotated OpenAPI 3
    schema downloading information from .

    :param schema: The schema to extract the information from.
    :return: The Turtle string.
    :rtype: str
    """
    jp_context = jsonpath_ng.parse("$..x-jsonld-context")
    fields = {
        "$.info.title": DCTERMS.title,
        "$.info.description": DCTERMS.description,
        "$.info.version": OWL.versionInfo,
        "$.info.contact.url": DCTERMS.rightsHolder,
        "$.info.contact.name": NS_FOAF.name,
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
    ret[DCAT.theme] = URIRef(
        "http://publications.europa.eu/resource/authority/data-theme/TECHNOLOGY"
    )
    domains = set()
    ontologies = set()
    rightsholder = {
        "@id": ret.pop(DCTERMS.rightsHolder, "MISSING"),
        NS_FOAF.name: ret.pop(NS_FOAF.name, "MISSING"),
    }
    for ctx in jp_context.find(schema):
        # Find all predicates related to NS_ITALIA.
        semantic_assets = get_schema_assets(ctx.value)

        domains = domains.union(
            {uri for _, _, uri in semantic_assets.triples((None, RDFS.domain, None))}
        )
        ontologies = ontologies.union(
            {
                uri
                for _, _, uri in semantic_assets.triples((None, RDFS.isDefinedBy, None))
            }
        )
    return {
        "domains": list(domains),
        "ontologies": list(ontologies),
        "rightsholder": rightsholder,
        **ret,
    }


def get_schema_assets(context: Dict) -> Graph:

    g = Graph()
    log.debug("Normalizing %r", context)
    try:
        data_normalized = jsonld.normalize(
            {"@context": context, **context},
            {"algorithm": "URDNA2015", "format": "application/nquads"},
        )
    except jsonld.JsonLdError:
        log.exception("Error processing jsonld context: %r" % (context,))
        raise
    g.parse(data=data_normalized)
    allowed_ns = (NS_ITALIA,)
    semantic_assets = {p for p in g.predicates() if p.startswith(*allowed_ns)}

    # Download all dependencies via IRI.
    semantic_dependencies = Graph()
    for p in semantic_assets:
        data = get_asset(str(p))
        semantic_dependencies += data

    # TODO: retrieve all dependencies from the current git repo.
    return semantic_dependencies


def oas3_to_turtle(
    schema_uri: str,
    schema: Dict,
    download_url: str,
    access_url: str = None,
    # rightsholder: Dict = None,
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
    rightsholder = semantic_references.pop("rightsholder")

    for k, v in semantic_references.items():
        g.add((dataset_uri, k, v))
    for o in ontologies:
        g.add((dataset_uri, DCTERMS.conformsTo, o))
    for cls in domains:
        g.add((dataset_uri, NS_ADMSAPT.hasKeyClass, cls))

    rh = URIRef(rightsholder["@id"])
    g.add((dataset_uri, DCTERMS.rightsHolder, rh))

    g.add((dataset_uri, RDF.type, NS_DCATAPIT.Dataset))
    g.add((dataset_uri, DCTERMS.modified, Literal(date.today().isoformat())))
    g.add((dataset_uri, DCAT.distribution, distribution_url))

    # Generate distribution properties
    log.debug("Generate distribution properties")
    [
        g.add(triple)
        for triple in [
            (distribution_url, RDF.type, NS_DCATAPIT.Distribution),
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

    for triple in [
        (rh, RDF.type, NS_FOAF.Agent),
        (rh, RDF.type, NS_DCATAPIT.Agent),
        (rh, NS_FOAF.name, Literal(rightsholder[NS_FOAF.name])),
        (rh, DCTERMS.identifier, Literal(rightsholder["@id"].split("/")[-1])),
    ]:
        g.add(triple)

    log.warning("Generated distribution: %s", g.serialize(format="turtle"))
    return g


def build_schema(fpath: Path, buildpath: Path = Path(".")):
    if fpath.suffix != ".yaml":
        raise ValueError(f"Not a yaml file: {fpath}")

    log.info(f"Building yaml asset for: {fpath}")
    oas_schema = yaml_load(fpath)
    asset = Asset(fpath)

    dpath = buildpath / fpath.parent / "index.ttl"
    dpath.parent.mkdir(exist_ok=True, parents=True)
    if not is_recent_than(fpath, dpath):
        return

    index_graph = oas3_to_turtle(
        asset.uri,
        oas_schema,
        access_url=asset.access_url,
        download_url=asset.download_url,
    )

    return index_graph.serialize(dpath.as_posix(), format="turtle")


def build_schema_vocabulary(fpath: Path, buildpath: Path = Path(".")):
    raise NotImplementedError
