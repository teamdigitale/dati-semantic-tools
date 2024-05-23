import json
import logging
from pathlib import Path

import git
import jsonschema
import yaml
from openapi_spec_validator import validate_spec
from pyshacl.validate import validate

from dati_playground.utils import MIME_JSONLD, is_recent_than, parse_graph
from dati_playground.validators import MAX_DEPTH, get_shacl_graph
from dati_playground.validators.csv import is_csv

log = logging.getLogger(__name__)


class Asset:
    def __init__(self, path: str, type: str = None, validate_repo=True):

        if type not in ["jsonschema", "graph", "oas3", "csv", None]:
            raise ValueError(f"Unsupported asset type: {type}")

        self.path = Path(path)

        if validate_repo:
            repo = git.Repo()
            self.path = self.path.absolute().relative_to(repo.working_tree_dir)
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
        if type:
            self.type = type
        elif self.path.name.endswith(
            (
                ".yaml",
                ".yml",
                ".json",
            )
        ):
            self.type = "schema"
        elif self.path.name.endswith((".ttl", ".jsonld")):
            self.type = "graph"
        elif self.path.name.endswith((".csv",)):
            self.type = "csv"
        else:
            raise NotImplementedError(f"Unsupported file suffix: {self.path.name}")

    def content(self):
        return self.path.read_text()

    def parse(self):
        if self.type == "schema":
            self.g = yaml.safe_load(self.content())
            if "openapi" in self.g:
                self.type = "oas3"
            return
        if self.type == "graph":
            self.g = parse_graph(self.path)
            return
        if self.type == "csv":
            self.g = self.path
            return

        raise NotImplementedError(f"Unsupported file suffix: {self.path.name}")

    def _validate_shacl(self, g):
        log.info("Validating {}".format(self.path))
        shacl_graph = None
        rule_path = None
        rule_dir = Path(self.path).parent
        for _ in range(MAX_DEPTH):
            rule_candidate = rule_dir / "rules.shacl"
            if rule_candidate.exists():
                rule_path = rule_candidate.absolute().as_posix()
                shacl_graph = get_shacl_graph(rule_path)
                log.info(f"Found shacl self.path: {rule_path}")
                break
            if rule_dir.name == "":
                break
            rule_dir = rule_dir.parent
        try:
            is_valid, graph, report_text = validate(g, shacl_graph=shacl_graph)
            log.info(f"Validation result: {is_valid}, {rule_path}, {report_text}")
            if not is_valid:
                raise ValueError(report_text)
        except Exception as e:
            log.error(f"Error validating {self.path}: {rule_path} {e}")
            raise

    def validate(self):
        v_map = {
            "schema": jsonschema.Draft7Validator.check_schema,
            "oas3": validate_spec,
            "graph": self._validate_shacl,
            "csv": is_csv,
        }
        if self.type not in v_map:
            raise NotImplementedError(f"Unsupported file suffix: {self.type}")
        validate = v_map[self.type]
        log.info(f"Validating {self.path} with {validate}")
        return validate(self.g)

    def _build_graph(self, dest_dir: Path = Path("."), preserve_tree=True):
        log.warning(f"Building {self.path} in {dest_dir}")

        built_files = []

        for args, ext in (
            ({"format": "pretty-xml", "max_depth": 1}, ".rdf"),
            (
                {"format": MIME_JSONLD, "auto_compact": True, "context_data": True},
                ".jsonld",
            ),
        ):
            if preserve_tree:
                dname = self.path
            else:
                dname = self.path.name
            dpath = (dest_dir / dname).with_suffix(ext)

            dpath.parent.mkdir(exist_ok=True, parents=True)
            if not is_recent_than(self.path, dpath):
                continue
            self.g.serialize(**args, destination=dpath.as_posix())
            built_files.append(dpath)
        return built_files

    def _build_schema(self, dest_dir: Path = Path(".")):
        log.info(f"Building yaml asset for: {self.path}")
        dsuffix = ".json"
        dpath_name = self.path.name
        if self.path.name.endswith(".ld.yaml"):
            dsuffix = ".jsonld"
            dpath_name = self.path.with_suffix("").name
        dpath = (dest_dir / self.path.parent / dpath_name).with_suffix(dsuffix)
        dpath.parent.mkdir(parents=True, exist_ok=True)
        dpath.write_text(json.dumps(self.g, indent=2))

    def serialize(self, format: str = "json"):
        if self.type in ("schema", "oas3"):
            if format == "json":
                return json.dumps(self.g, indent=2)
            if format == "yaml":
                return yaml.safe_dump(self.g, indent=2)
        if self.type == "graph":
            if format == "yaml":
                return yaml.safe_dump(
                    json.loads(self.g.serialize(format="application/ld+json"))
                )
            return self.g.serialize(format=format)
        raise NotImplementedError(f"Unsupported file suffix: {self.self.path.name}")

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
