#!/usr/bin/env python3

from __future__ import annotations

import ipaddress
from pathlib import Path


DOCS_DIR = Path("docs")
AGGREGATE_DIR = DOCS_DIR / "aggregate"
AZURE_DIR = DOCS_DIR / "azure"
O365_DIR = DOCS_DIR / "o365"
GITHUB_FILE = DOCS_DIR / "github.txt"


def read_networks(file_path: Path) -> set[str]:
    if not file_path.exists():
        return set()

    networks: set[str] = set()
    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ipaddress.ip_network(line, strict=False)
        networks.add(line)
    return networks


def split_ip_versions(networks: set[str]) -> tuple[list[str], list[str]]:
    ipv4: list[str] = []
    ipv6: list[str] = []

    for network in sorted(networks, key=sort_key):
        parsed = ipaddress.ip_network(network, strict=False)
        if parsed.version == 4:
            ipv4.append(network)
        else:
            ipv6.append(network)

    return ipv4, ipv6


def sort_key(network: str) -> tuple[int, int, int, str]:
    parsed = ipaddress.ip_network(network, strict=False)
    return (parsed.version, int(parsed.network_address), parsed.prefixlen, network)


def write_networks(file_path: Path, networks: set[str]) -> None:
    ipv4, ipv6 = split_ip_versions(networks)
    combined = ipv4 if file_path.stem.endswith("ipv4") else ipv6
    file_path.write_text("".join(f"{network}\n" for network in combined), encoding="utf-8")


def collect_azure_networks() -> set[str]:
    networks: set[str] = set()
    for file_path in AZURE_DIR.glob("*.txt"):
        networks.update(read_networks(file_path))
    return networks


def collect_o365_networks(pattern: str) -> set[str]:
    networks: set[str] = set()
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
