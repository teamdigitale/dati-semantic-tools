import logging
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Dict

import jsonpath_ng
import jsonschema
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
    asset = get(netloc, headers={"Accept": "text/turtle"})
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
    rightsholder = {
        "@id": ret.pop(DCTERMS.rightsHolder, "MISSING"),
        NS_FOAF.name: ret.pop(NS_FOAF.name, "MISSING"),
    }
    domains, ontologies = get_context_references(schema)
    return {
        "domains": list(domains),
        "ontologies": list(ontologies),
        "rightsholder": rightsholder,
        **ret,
    }


def get_semantic_summary(context: Dict):
    semantic_assets = get_schema_assets(context)

    return {
        "domains": {
            uri for _, _, uri in semantic_assets.triples((None, RDFS.domain, None))
        },
        "ontologies": {
            uri for _, _, uri in semantic_assets.triples((None, RDFS.isDefinedBy, None))
        },
    }


def get_context_references(schema: Dict):
    """Return a list of semantic references from an OAS3 specification."""
    jp_context = jsonpath_ng.parse("$..x-jsonld-context")
    domains = set()
    ontologies = set()
    for ctx in jp_context.find(schema):
        # Find all predicates related to NS_ITALIA.
        semantic_assets = get_semantic_summary(ctx.value)

        domains = domains.union(semantic_assets["domains"])
        ontologies = ontologies.union(semantic_assets["ontologies"])

    return domains, ontologies


def get_schema_assets(context: Dict, allowed_ns=(NS_ITALIA,)) -> Graph:

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
    semantic_assets = {p for p in g.predicates() if p.startswith(*allowed_ns)}

    # Download all dependencies via IRI.
    semantic_dependencies = Graph()
    for p in semantic_assets:
        data = get_asset(str(p))
        semantic_dependencies += data
    #
    # TODO: retrieve all dependencies from the current git repo.
    #
    expected_assets = set(semantic_assets)
    actual_assets = set(semantic_dependencies.subjects())
    missing_assets = expected_assets - actual_assets
    for missing in missing_assets:
        if not any(missing in y for y in actual_assets):
            log.warning(f"Missing asset: {missing}")
            raise ValueError(
                "Missing dependencies for %r in %r"
                % (
                    expected_assets - actual_assets,
                    allowed_ns,
                )
            )

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


def get_context_info(spec: Dict):
    jp_context = jsonpath_ng.parse("$..x-jsonld-context")
    for ctx in jp_context.find(spec):
        context = ctx.value
        schema_fragment = get_context_jsonpointer(ctx)
        schema_content = ctx.context.value

        # Validate the schema. It throws in case of exceptions.
        jsonschema.Draft7Validator.check_schema(schema_content)

        yield schema_fragment, schema_content, context


def get_context_jsonpointer(ctx):
    return "#/" + "/".join(_dump(ctx.full_path.left))


def _dump(full_path):
    if hasattr(full_path, "left"):
        yield from _dump(full_path.left)
    if hasattr(full_path, "right"):
        yield from _dump(full_path.right)
    else:
        yield full_path.fields[0]


def validate_context(context, allowed_ns=(NS_ITALIA,)):
    assets = get_schema_assets(context, allowed_ns=allowed_ns)
    subjects = set(s for s in assets.subjects() if s.startswith(*allowed_ns))
    ret = {}
    # import pdb; pdb.set_trace()
    for s in subjects:
        ((_, _, onto), *_) = assets.triples((s, RDFS.isDefinedBy, None))
        ((_, _, version_info), *_) = assets.triples((s, OWL.versionInfo, None))
        try:
            ((_, _, domain), *_) = assets.triples((s, RDFS.domain, None))
        except (ValueError,):
            domain = s

        data = get_asset(str(onto))
        ((_, _, last_modified), *_) = data.triples((None, DCTERMS.modified, None))
        ret[str(s)] = {
            "last_modified": str(last_modified),
            "domain": str(domain),
            "version_info": str(version_info),
            "onto": str(onto),
            "subject": str(s),
        }
    return ret


def ndc_semantic_bundle(spec: Dict):
    ret = {
        "title": spec["info"]["title"],
        "schema_total": len(spec.get("components", {}).get("schemas", {})),
        "schema_covered": 0,
        "assets": {},
    }
    for schema_fragment, schema_content, context in get_context_info(spec):
        ret["schema_covered"] += 1
        properties_total, properties_semantic = [], []
        if schema_content.get("type") != "object":
            # const, oneOf, anyOf, allOf are not supported.
            # string, number, integer, boolean, null, array, object are supported.
            raise NotImplementedError

        properties = schema_content.get("properties", {})
        for property_name, property_schema in properties.items():
            if property_schema.get("type") in ("object", "array"):
                # only basic types are supported.
                pass  # raise NotImplementedError
            properties_total.append(property_name)
            if context.get(property_name):
                properties_semantic.append(property_name)

        assets = get_semantic_summary(context)
        ret.update(
            {
                schema_fragment: {
                    "properties_score": (
                        len(properties_semantic),
                        len(properties_total),
                    ),
                    "assets": {k: [str(x) for x in v] for k, v in assets.items()},
                }
            }
        )

        for asset_name, asset_value in validate_context(context).items():
            if asset_name not in ret["assets"]:
                ret["assets"][asset_name] = {"referrer": []}
            ret["assets"][asset_name].update(asset_value)
            ret["assets"][asset_name]["referrer"].append(schema_fragment)

    return ret
