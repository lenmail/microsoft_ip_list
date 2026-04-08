#!/usr/bin/env python3

from __future__ import annotations

import ipaddress
from pathlib import Path


DOCS_DIR = Path("docs")
AGGREGATE_DIR = DOCS_DIR / "aggregate"
AZURE_DIR = DOCS_DIR / "azure"
O365_DIR = DOCS_DIR / "o365"
GITHUB_FILE = DOCS_DIR / "github.txt"


def read_networks(file_path: Path) -> set[ipaddress._BaseNetwork]:
    if not file_path.exists():
        return set()

    networks: set[ipaddress._BaseNetwork] = set()
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        networks.add(ipaddress.ip_network(line, strict=False))
    return networks


def sort_key(network: ipaddress._BaseNetwork) -> tuple[int, int, int, str]:
    return (network.version, int(network.network_address), network.prefixlen, str(network))


def collapse_networks(networks: set[ipaddress._BaseNetwork], version: int) -> list[ipaddress._BaseNetwork]:
    filtered = [network for network in networks if network.version == version]
    return sorted(ipaddress.collapse_addresses(filtered), key=sort_key)


def write_networks(file_path: Path, networks: set[ipaddress._BaseNetwork]) -> None:
    version = 4 if file_path.stem.endswith("ipv4") else 6
    collapsed = collapse_networks(networks, version)
    file_path.write_text("".join(f"{network}\n" for network in collapsed), encoding="utf-8")


def collect_azure_networks() -> set[ipaddress._BaseNetwork]:
    networks: set[ipaddress._BaseNetwork] = set()
    for file_path in AZURE_DIR.glob("*.txt"):
        networks.update(read_networks(file_path))
    return networks


def collect_o365_networks(pattern: str) -> set[ipaddress._BaseNetwork]:
    networks: set[ipaddress._BaseNetwork] = set()
    for file_path in O365_DIR.glob(pattern):
        networks.update(read_networks(file_path))
    return networks


def main() -> None:
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)

    github_networks = read_networks(GITHUB_FILE)
    azure_networks = collect_azure_networks()
    o365_tcp_networks = collect_o365_networks("tcp_*.txt")
    o365_udp_networks = collect_o365_networks("udp_*.txt")
    o365_mixed_networks = collect_o365_networks("*_udp_*.txt")

    all_networks = github_networks | azure_networks | o365_tcp_networks | o365_udp_networks | o365_mixed_networks
    tcp_networks = github_networks | azure_networks | o365_tcp_networks | o365_mixed_networks
    udp_networks = o365_udp_networks | o365_mixed_networks

    output_sets = {
        "all_ipv4.txt": all_networks,
        "all_ipv6.txt": all_networks,
        "tcp_ipv4.txt": tcp_networks,
        "tcp_ipv6.txt": tcp_networks,
        "udp_ipv4.txt": udp_networks,
        "udp_ipv6.txt": udp_networks,
    }

    for file_name, networks in output_sets.items():
        write_networks(AGGREGATE_DIR / file_name, networks)


if __name__ == "__main__":
    main()
