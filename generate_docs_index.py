#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
GENERATED_FILE = DOCS_DIR / "generated.txt"
INDEX_FILE = DOCS_DIR / "index.md"


def iter_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.name != "endpoints_clientid_latestversion.txt"
    )


def format_link(path: Path) -> str:
    relative_path = path.relative_to(DOCS_DIR).as_posix()
    return f"* [{relative_path}]({quote(relative_path)})"


def main() -> None:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    GENERATED_FILE.write_text(f"{generated_at}\n", encoding="utf-8")

    sections = [
        ("GitHub", [DOCS_DIR / "github.txt"]),
        ("Azure Service Tags", iter_files(DOCS_DIR / "azure")),
        ("Microsoft 365 Endpoints", iter_files(DOCS_DIR / "o365")),
    ]

    lines = [
        "# Microsoft Service Endpoint Lists",
        "",
        "This index is generated from the current repository content.",
        "The transient generation timestamp is written to `docs/generated.txt` during each run and is not tracked in Git.",
    ]

    for heading, files in sections:
        if not files:
            continue
        lines.extend(["", f"## {heading}", ""])
        lines.extend(format_link(path) for path in files)

    INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
