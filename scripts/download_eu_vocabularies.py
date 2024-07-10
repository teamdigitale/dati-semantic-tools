import logging
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from rdflib.graph import Graph

log = logging.getLogger(__name__)


query = """
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX odp:  <http://data.europa.eu/euodp/ontologies/ec-odp#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT distinct ?u WHERE {

?s a dcat:Dataset .
?s dcat:distribution ?d .
?d a dcat:Distribution .
?d dct:format <http://publications.europa.eu/resource/authority/file-type/RDF_XML>  .
  ?d dcat:downloadURL ?u FILTER regex(?u, "-skos.rdf$", "i" )
} LIMIT 100
"""

url = "https://data.europa.eu/sparql"


def sparql_get(sparql_endpoint, query):
    qp = {
        "query": [query],
        "format": ["application/sparql-results+json"],
        "timeout": ["0"],
        "debug": ["on"],
        "run": [" Run Query "],
    }

    ep = urlencode(qp, doseq=True)
    data = requests.get(f"{sparql_endpoint}?" + ep, timeout=10)
    return data.json()


def get_vocabularies(url):
    ret = sparql_get(url, query)
    for download_url in [x["u"]["value"] for x in ret["results"]["bindings"]]:
        url = urlparse(download_url)
        try:
            file_name = parse_qs(url.query)["fileName"][0]
            dest_file = Path(file_name.replace("-skos", ""))
            dest_file = (
                Path("assets") / "vocabularies" / dest_file.stem / "latest" / dest_file
            ).with_suffix(".ttl")
            yield download_url, dest_file
        except (KeyError, IndexError):
            print(f"Cannot parse {download_url}")


def download_file(url, dest_file):
    print(url, dest_file)
    g = Graph()
    data = requests.get(url, timeout=10)
    if data.status_code != 200:
        log.error(f"Erro retrieving {url}: {data.status_code}")
        return

    file_rdf = dest_file.with_suffix(".rdf")
    file_rdf.write_bytes(data.content)
    g.parse(file_rdf.as_posix(), format="application/rdf+xml")
    dest_file.parent.mkdir(exist_ok=True, parents=True)
    g.serialize(format="text/turtle", destination=dest_file.as_posix())


if __name__ == "__main__":
    from multiprocessing import Pool
    from sys import argv

    needle = argv[1] if argv[1:] else ""
    workers = Pool(processes=20)
    workers.starmap(
        download_file, ((x, y) for x, y in get_vocabularies(url) if needle in x)
    )
    workers.close()
