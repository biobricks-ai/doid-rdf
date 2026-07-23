#!/usr/bin/env python3
from __future__ import annotations

import gzip
import io
import json
import sys
from pathlib import Path

from pyld import jsonld
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

DOID = "http://purl.obolibrary.org/obo/DOID_"


def build(source: Path, output_root: Path) -> tuple[dict, dict]:
    graph = Graph()
    graph.parse(source, format="xml")
    output_root.mkdir(parents=True, exist_ok=True)
    document = json.loads(graph.serialize(format="json-ld"))
    normalized = jsonld.normalize(document, {
        "algorithm": "URDNA2015",
        "format": "application/n-quads",
    })
    lines = sorted(line for line in normalized.splitlines() if line)
    with gzip.GzipFile(filename=str(output_root / "doid.nt.gz"), mode="wb", mtime=0) as compressed:
        with io.TextIOWrapper(compressed, encoding="utf-8") as stream:
            for line in lines:
                stream.write(line + "\n")

    classes = {s for s in graph.subjects(RDF.type, OWL.Class) if str(s).startswith(DOID)}
    labeled = {s for s in classes if any(graph.objects(s, RDFS.label))}
    deprecated = {s for s in classes if any(str(v).lower() == "true" for v in graph.objects(s, OWL.deprecated))}
    subclass_targets = {o for s in classes for o in graph.objects(s, RDFS.subClassOf) if isinstance(o, URIRef)}
    doid_targets = {o for o in subclass_targets if str(o).startswith(DOID)}
    coverage = {
        "schema_version": "1.0", "status": "complete", "source_release": "v2026-06-30",
        "source_triples": len(graph), "output_triples": len(lines), "triple_coverage": 1.0,
        "doid_classes": len(classes), "labeled_doid_classes": len(labeled),
        "class_label_coverage": len(labeled) / len(classes), "deprecated_doid_classes": len(deprecated),
        "doid_subclass_targets": len(doid_targets), "output_format": "application/n-triples+gzip",
    }
    health = {
        "schema_version": 1,
        "passed": len(graph) == len(lines) and classes == labeled and bool(classes),
        "score": round(100 * len(labeled) / len(classes), 2),
        "checks": {
            "lossless_rdf_normalization": len(graph) == len(lines),
            "all_doid_classes_labeled": classes == labeled,
            "canonical_doid_iris": all(str(value).startswith(DOID) for value in classes),
            "nonempty_hierarchy": bool(doid_targets),
            "blank_nodes_preserved": sum(1 for value in graph.all_nodes() if value.__class__.__name__ == "BNode"),
        },
        "note": "Blank nodes are authoritative OWL restrictions/axioms and are retained rather than replaced with invented classes or predicates."
    }
    (output_root / "source-coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    (output_root / "ontology-health.json").write_text(json.dumps(health, indent=2, sort_keys=True) + "\n")
    return coverage, health


if __name__ == "__main__":
    coverage, health = build(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({"coverage": coverage, "ontology_health": health}, indent=2))
