# Playground for json-schema and RDF

This repo contains code and samples to experiment with attaching semantic metadata to
payloads exchanged via APIs.

For readability:

- all json files are serialized as yaml
- all RDF files are serialized as text/turtle
- all semantic assets to be harvested/published are in
  `assets/`; files outside this directory should be safely
  ignored by other entities and are either used for testing
  or for developing and validating what's in `assets/`

Asset documentation can be provided inside turtle files
and via makdown files (eg. to better describe each specific development
process).

## Structure

Repo contains the following files.

```text
├── publiccode.yaml            # Repository reuse metadata
├── ndc-config.yaml            # Harvest configuration file
├── assets                     # Semantic assets
│   ├── ontologies
│   ├── schemas
│   │   ├── birth_certificate
│   │   ├── person
│   └── vocabularies
│       └── countries
├── examples
├── playground                 # The python code
│   ├── data                   #   datafiles for the playground
├── tests
    ├── data                   #   test datafiles
├── docker-compose.yml         # Local sparql server
├── Dockerfile
├── sparql
└── scripts                    # Syntax checks & co
```

## Development

This repository uses pre-commit to validate content.
An integrated testing environment to reproduce the CI pipeline
is available via docker-compose, which goes on thru a set of steps.

```bash
docker-compose -f docker-compose-test.yml up
```

## Tests

Generate assets in different formats

- yaml -> json
- ttl -> ntriple, rdf+xml, jsonld

Generate RDF from json-schema

## pre-commit hooks

To test pre-commit hooks developed in this repo,
just run

```bash
pre-commit try-repo . -a
```
