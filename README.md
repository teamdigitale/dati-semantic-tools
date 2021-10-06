# Playground for json-schema and RDF

This repo contains code and samples to experiment with attaching semantic metadata to
payloads exchanged via APIs.

For readability:

- all json files are serialized as yaml
- all RDF files are serialized as text/turtle

## Structure

Repo contains the following files.

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

## Tests

Generate assets in different formats

- yaml -> json
- ttl -> ntriple, rdf+xml, jsonld

Generate RDF from json-schema
