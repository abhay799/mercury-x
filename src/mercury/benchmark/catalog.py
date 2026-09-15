import json
from pathlib import Path

from .models import BenchmarkCatalog


def load_benchmark_catalog(path: str | Path) -> BenchmarkCatalog:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return BenchmarkCatalog.model_validate(payload)
