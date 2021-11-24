# The Person schema.

This folder contains a `Person` schema model in different formats, including:

- openapi 3.0;
- json-schema 2011.

These schemas can be used to model entities according to the [Person](https://w3id.org/italia/onto/CPV/Person)
ontology.

All json-related schemas are serialized using yaml format because:

- it allows adding comments into the files;
- yaml syntax avoids some json pitfalls such as duplicate keys.
JSON-serialized files can be derived from yaml ones.

Since json-schema and its derivates (eg. OAS3) are focused on
efficient parsing and do not natively
support the addition of semantic metadata to entries,
each schema is integrated with a specific json-ld context file
that can be used to document and verify the semantics of any
json data conformant to the schema.

Example files contains:

- person.example.yaml  # a json object where the payload component
  syntax is valid according to the schema definition, and a "@context"
  component that can be used to identify all semantic-related assets;
- person.example.ttl  # a text/turtle file derived from person.example.yaml
  data and translated in RDF format.

## OAS3.0

File: person.oas3.yaml

OAS3.0 schema files are embedded in the `#/components/schemas` json-path
fragment of an OpenAPI file to allow the reuse of OpenAPI validation tools
such as [api-oas-checker]() and to avoid errors in code-generation tools.

An OAS3 schema file MUST end with "oas3.yaml".


## JsonSchema

File: person.schema.yaml



```
.
├── index.ttl
├── person.example.ttl
├── person.example.yaml
├── person.ld.yaml
├── person.oas3.yaml
└── person.schema.yaml
```
