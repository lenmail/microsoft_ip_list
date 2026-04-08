#!/usr/bin/env python3

from __future__ import annotations

import ipaddress
import json
from pathlib import Path
from urllib.request import Request, urlopen


META_URL = "https://api.github.com/meta"
OUTPUT_FILE = Path("docs/github.txt")


def fetch_meta() -> dict:
    request = Request(
        META_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "lenmail-microsoft-ip-list-generator",
        },
    )
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_networks(meta: dict) -> set[str]:
    networks: set[str] = set()
    for value in meta.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, str):
                continue
            try:
                ipaddress.ip_network(item, strict=False)
            except ValueError:
                continue
            networks.add(item)
    return networks


def sort_key(network: str) -> tuple[int, int, int, str]:
    parsed = ipaddress.ip_network(network, strict=False)
    return (parsed.version, int(parsed.network_address), parsed.prefixlen, network)


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    meta = fetch_meta()
    networks = sorted(iter_networks(meta), key=sort_key)
    OUTPUT_FILE.write_text(
        "".join(f"{network}\n" for network in networks),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
