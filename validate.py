"""
validate.py
"""
import os
from pathlib import Path

from playground import validators

valid_suffixes = {
    ".ttl": validators.is_turtle,
    ".ld.yaml": validators.is_jsonld,
    ".oas3.yaml": validators.is_openapi,
    ".schema.yaml": validators.is_jsonschema,
}

skip_suffixes = (".md", ".csv", ".png", ".xml", ".xsd")


def validate_file(f: str):
    f = Path(f).absolute()

    for suffix, is_valid in valid_suffixes.items():
        if f.stat().st_size > 1 << 20:
            raise ValueError(f"File too big: {f.size}")
        if f.name.endswith(suffix):
            print(f"Validating {f}")
            if is_valid(f.read_text()):
                return True
            else:
                raise ValueError(f"Invalid file: {f}")
    raise ValueError(f"Unsupported file {f}")


if __name__ == "__main__":
    basepath = Path("assets")

    for root, dirs, files in os.walk(basepath):
        for f in files:
            if f.endswith(skip_suffixes):
                continue
            if f == "index.ttl":
                continue
            validate_file(os.path.join(root, f))
