import gzip
import hashlib
import json
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from stages.acquire import SHA256, SIZE

ROOT = Path(__file__).parents[1]
DOID = "http://purl.obolibrary.org/obo/DOID_"


def test_structured_metadata_and_license():
    source = json.loads((ROOT / ".bb/source.jsonld").read_text())
    brick = json.loads((ROOT / ".bb/brick.jsonld").read_text())
    assert source["dcterms:license"]["@id"] == "https://creativecommons.org/publicdomain/zero/1.0/"
    assert source["dcterms:hasVersion"] == "v2026-06-30"
    assert source["dcat:distribution"]["spdx:checksum"]["spdx:checksumValue"] == SHA256
    assert brick["prov:wasDerivedFrom"]["@id"] == source["@id"]
    artifact = ROOT / brick["dcat:distribution"]["dcat:downloadURL"]
    assert artifact.stat().st_size == brick["dcat:distribution"]["dcat:byteSize"]
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == brick["dcat:distribution"]["spdx:checksum"]["spdx:checksumValue"]
    Graph().parse(ROOT / ".bb/source.jsonld", format="json-ld")
    Graph().parse(ROOT / ".bb/brick.jsonld", format="json-ld")


def test_acquired_source_integrity():
    source = ROOT / "source/doid.owl"
    assert source.stat().st_size == SIZE
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SHA256


def test_production_output_parses_and_is_complete():
    report = json.loads((ROOT / "brick/source-coverage.json").read_text())
    health = json.loads((ROOT / "brick/ontology-health.json").read_text())
    graph = Graph()
    with gzip.open(ROOT / "brick/doid.nt.gz", "rt", encoding="utf-8") as stream:
        graph.parse(stream, format="nt")
    assert len(graph) == report["source_triples"] == report["output_triples"] == 306890
    assert report["triple_coverage"] == report["class_label_coverage"] == 1
    assert health["passed"] and health["checks"]["lossless_rdf_normalization"]


def test_canonical_disease_identifiers_and_labels():
    graph = Graph()
    graph.parse(ROOT / "source/doid.owl", format="xml")
    disease = URIRef(DOID + "4")
    assert (disease, RDF.type, OWL.Class) in graph
    assert str(graph.value(disease, RDFS.label)) == "disease"
    classes = {s for s in graph.subjects(RDF.type, OWL.Class) if str(s).startswith(DOID)}
    assert len(classes) == 14735
    assert all(any(graph.objects(term, RDFS.label)) for term in classes)


def test_checked_in_health_contracts():
    coverage = json.loads((ROOT / "health/source-coverage.json").read_text())
    policy = json.loads((ROOT / "health/ontology-policy.json").read_text())
    status = json.loads((ROOT / "health/build-status.json").read_text())
    assert coverage["profile"] == policy["profile"] == status["profile"] == "reference-ontology-import"
    assert coverage["tabular_conversion_coverage"] == "not-applicable"
    assert policy["schema_ownership"] == "upstream Disease Ontology"
    assert status["status"] == "validated-reference-import"
    assert status["artifact_publication"] == "deferred-by-project-policy"
    assert status["artifact_location"] == "local DVC cache"
    assert status["blocker"] is None
