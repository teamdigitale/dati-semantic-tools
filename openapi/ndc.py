import hashlib

import yaml

from dati_playground.schema import ndc_semantic_bundle
from dati_playground.validators import is_openapi


def post_semantic_coverage(body):
    spec = yaml.safe_load(body)

    is_openapi(body)

    ret = ndc_semantic_bundle(spec)
    return {"spec": len(body), "sha-256": hashlib.sha256(body).hexdigest(), "ret": ret}
