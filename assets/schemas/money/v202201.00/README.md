# The Money schema.

This folder contains a `Money` schema model in different formats, including:

- openapi 3.0;

These schemas can be used to model entities according to the [Money](https://w3id.org/italia/onto/POT)
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

Schema file contains an `example` json object where the payload component
  syntax is valid according to the schema definition, and a "@context"
  component that can be used to identify all semantic-related assets;

There is no `text/turtle` file derived from the example
  data and translated in RDF format.

## OAS3.0

File: money.oas3.yaml

OAS3.0 schema files are embedded in the `#/components/schemas` json-path
fragment of an OpenAPI file to allow the reuse of OpenAPI validation tools
such as [api-oas-checker]() and to avoid errors in code-generation tools.

An OAS3 schema file MUST end with "oas3.yaml".


## JsonSchema

There's no jsonschema file.



```
.
├── index.ttl
├── money.oas3.yaml
├── person.ld.yaml
└── README.md
```
