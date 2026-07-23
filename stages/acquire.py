#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://raw.githubusercontent.com/DiseaseOntology/HumanDiseaseOntology/v2026-06-30/src/ontology/doid.owl"
SHA256 = "2c25743800b059326b4c318e83a52803b58fdf8720746921cc292afdac0f7e4e"
SIZE = 28_480_371


def acquire(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".download")
    digest = hashlib.sha256()
    size = 0
    try:
        with urllib.request.urlopen(URL, timeout=120) as response, temporary.open("wb") as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
                digest.update(chunk)
                size += len(chunk)
        if size != SIZE or digest.hexdigest() != SHA256:
            raise ValueError(f"source integrity failure: {size} bytes, sha256 {digest.hexdigest()}")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    acquire(Path(sys.argv[1]))
