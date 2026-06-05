from __future__ import annotations

import argparse
from pathlib import Path
import re


REGISTRY_IMPORT = "from .ca3 import Ca3MemoryProvider\n"
REGISTRY_ENTRY = '    "ca3": Ca3MemoryProvider,\n'


PROVIDER_TEMPLATE = '''from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_CA3_ROOT = Path({ca3_root!r})
if str(_CA3_ROOT) not in sys.path:
    sys.path.insert(0, str(_CA3_ROOT))

from ca3.benchmarks.amb_provider import Ca3OpenMemoryBenchmarkProvider, records_to_omb_documents
from .base import MemoryProvider
from ..models import Document


class Ca3MemoryProvider(MemoryProvider):
    name = "ca3"
    description = "CA3 deterministic local MemoryBackend provider."
    kind = "local"
    provider = "ca3"
    variant = "local"
    concurrency = 1

    def __init__(self) -> None:
        self._provider = Ca3OpenMemoryBenchmarkProvider()

    def prepare(self, store_dir: Path, unit_ids: set[str] | None = None, reset: bool = True) -> None:
        self._provider.prepare(store_dir, unit_ids=unit_ids, reset=reset)

    def ingest(self, documents: list[Document]) -> None:
        self._provider.ingest(documents)

    def retrieve(
        self,
        query: str,
        k: int = 10,
        user_id: str | None = None,
        query_timestamp: str | None = None,
    ) -> tuple[list[Document], dict[str, Any]]:
        records, raw_response = self._provider.retrieve(
            query,
            k=k,
            user_id=user_id,
            query_timestamp=query_timestamp,
        )
        return records_to_omb_documents(records, Document), raw_response
'''


def install_provider(omb_checkout: str | Path, ca3_root: str | Path) -> list[Path]:
    omb_checkout = Path(omb_checkout).resolve()
    ca3_root = Path(ca3_root).resolve()
    memory_dir = omb_checkout / "src" / "memory_bench" / "memory"
    init_path = memory_dir / "__init__.py"
    provider_path = memory_dir / "ca3.py"

    if not memory_dir.exists():
        raise FileNotFoundError(f"OMB memory provider directory not found: {memory_dir}")
    if not init_path.exists():
        raise FileNotFoundError(f"OMB memory registry not found: {init_path}")
    if not (ca3_root / "ca3").exists():
        raise FileNotFoundError(f"ca3 package root not found: {ca3_root}")

    provider_path.write_text(PROVIDER_TEMPLATE.format(ca3_root=str(ca3_root)), encoding="utf-8")

    init_text = init_path.read_text(encoding="utf-8")
    if REGISTRY_IMPORT not in init_text:
        last_import = "from .supermemory import SupermemoryMemoryProvider\n"
        if last_import in init_text:
            init_text = init_text.replace(last_import, last_import + REGISTRY_IMPORT)
        else:
            init_text = REGISTRY_IMPORT + init_text

    if REGISTRY_ENTRY not in init_text:
        pattern = re.compile(r"REGISTRY: dict\[str, type\[MemoryProvider\]\] = \{\n")
        init_text, replacements = pattern.subn(lambda match: match.group(0) + REGISTRY_ENTRY, init_text, count=1)
        if replacements != 1:
            raise RuntimeError("Could not find OMB REGISTRY declaration to patch")

    init_path.write_text(init_text, encoding="utf-8")
    return [provider_path, init_path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install/register the ca3 provider into an Open Memory Benchmark checkout.")
    parser.add_argument("--omb-checkout", required=True, help="Path to vectorize-io/open-memory-benchmark checkout.")
    parser.add_argument(
        "--ca3-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="Path to ca3 repository root. Defaults to the current installed source checkout.",
    )
    args = parser.parse_args(argv)
    modified = install_provider(args.omb_checkout, args.ca3_root)
    for path in modified:
        print(path)
    print("Installed ca3 provider into Open Memory Benchmark. Next: uv run amb providers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
