# doid-rdf

Production graph brick for the Identifiers.org `doid` namespace. It packages the authoritative Human Disease Ontology release `v2026-06-30` as deterministic, gzip-compressed N-Triples.

The source release is pinned to commit `61d841a69c2b45a3f50214fb387263b5e99ba078`, verified by byte count and SHA-256, and licensed [CC0-1.0](https://github.com/DiseaseOntology/HumanDiseaseOntology/blob/main/LICENSE). The graph retains the upstream ontology without inventing local disease classes, predicates, or identifier aliases.

```sh
uv sync --extra test
uv run python stages/acquire.py source/doid.owl
uv run python stages/build.py source/doid.owl brick
uv run pytest -q
```

The release contains 306,890 statements and 14,735 canonical `http://purl.obolibrary.org/obo/DOID_…` classes. All DOID classes have labels. Authoritative OWL restrictions and axiom annotations use blank nodes; the build applies the RDF Dataset Canonicalization algorithm URDNA2015 so repeated builds are byte-for-byte reproducible.

Coverage for a reference ontology means faithful RDF import, not tabular-cell conversion. The build requires equal source/output statement counts, complete labels for DOID classes, a nonempty DOID hierarchy, strict source integrity, and successful parsing of the production artifact.
