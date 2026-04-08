#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
AZURE_DIR = DOCS_DIR / "azure"
O365_DIR = DOCS_DIR / "o365"
AGGREGATE_DIR = DOCS_DIR / "aggregate"
GITHUB_FILE = DOCS_DIR / "github.txt"
GENERATED_FILE = DOCS_DIR / "generated.txt"
INDEX_FILE = DOCS_DIR / "index.md"
VERSION_FILE = O365_DIR / "endpoints_clientid_latestversion.txt"

AZURE_SERVICE_TAGS_PAGE = "https://www.microsoft.com/en-us/download/details.aspx?id=56519"
GITHUB_META_URL = "https://api.github.com/meta"
O365_WEB_SERVICE = "https://endpoints.office.com"
O365_INSTANCE = "Worldwide"
O365_ALLOWED_CATEGORIES = {"Optimize", "Allow"}


IPAddressNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network


def http_get_text(url: str, headers: dict[str, str] | None = None) -> str:
    request = Request(url, headers=headers or {})
    with urlopen(request) as response:
        return response.read().decode("utf-8")


def http_get_json(url: str, headers: dict[str, str] | None = None) -> object:
    return json.loads(http_get_text(url, headers=headers))


def sort_network_key(network: IPAddressNetwork) -> tuple[int, int, int, str]:
    return (network.version, int(network.network_address), network.prefixlen, str(network))


def write_network_file(file_path: Path, networks: Iterable[IPAddressNetwork | str]) -> None:
    normalized = []
    for network in networks:
        parsed = ipaddress.ip_network(network, strict=False) if isinstance(network, str) else network
        normalized.append(parsed)
    file_path.write_text("".join(f"{network}\n" for network in normalized), encoding="utf-8")


def iter_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.rglob("*")
        if path.is_file() and path.name != "endpoints_clientid_latestversion.txt"
    )


def format_link(path: Path) -> str:
    relative_path = path.relative_to(DOCS_DIR).as_posix()
    return f"* [{relative_path}]({quote(relative_path)})"


def generate_azure_lists() -> None:
    AZURE_DIR.mkdir(parents=True, exist_ok=True)

    page_content = http_get_text(AZURE_SERVICE_TAGS_PAGE)
    match = re.search(r'https://download\.microsoft\.com/download/[^"]+ServiceTags_Public_[0-9]+\.json', page_content)
    if not match:
        raise RuntimeError("Could not determine the current Azure Service Tags download URL.")

    service_tags = http_get_json(match.group(0))
    grouped_networks: dict[str, set[str]] = defaultdict(set)

    for entry in service_tags["values"]:
        properties = entry.get("properties", {})
        if properties.get("region") != "":
            continue
        for prefix in properties.get("addressPrefixes", []):
            grouped_networks[entry["name"]].add(prefix)

    for name, networks in sorted(grouped_networks.items()):
        if not networks:
            print(f"No address prefixes found for {name}.", file=sys.stderr)
            continue
        write_network_file(
            AZURE_DIR / f"{name}.txt",
            sorted((ipaddress.ip_network(network, strict=False) for network in networks), key=sort_network_key),
        )


def generate_github_list() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    meta = http_get_json(
        GITHUB_META_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "lenmail-microsoft-ip-list-generator",
        },
    )

    networks: set[IPAddressNetwork] = set()
    for value in meta.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, str):
                continue
            try:
                networks.add(ipaddress.ip_network(item, strict=False))
            except ValueError:
                continue

    write_network_file(GITHUB_FILE, sorted(networks, key=sort_network_key))


def o365_api_get(method_name: str, client_request_id: str) -> object:
    query = urlencode({"clientRequestId": client_request_id})
    return http_get_json(f"{O365_WEB_SERVICE}/{method_name}/{O365_INSTANCE}?{query}")


def load_o365_version_state() -> tuple[str, str]:
    if VERSION_FILE.exists():
        lines = VERSION_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) >= 2 and lines[0] and lines[1]:
            return lines[0], lines[1]

    client_request_id = str(uuid.uuid4())
    latest_version = "0000000000"
    VERSION_FILE.write_text(f"{client_request_id}\n{latest_version}\n", encoding="utf-8")
    return client_request_id, latest_version


def write_o365_version_state(client_request_id: str, latest_version: str) -> None:
    VERSION_FILE.write_text(f"{client_request_id}\n{latest_version}\n", encoding="utf-8")


def normalize_port_group(ports: str) -> str:
    return "_".join(part.strip() for part in ports.split(",") if part.strip())


def reset_o365_port_files() -> None:
    for pattern in ("tcp_*.txt", "udp_*.txt", "*_udp_*.txt"):
        for file_path in O365_DIR.glob(pattern):
            file_path.unlink()


def generate_o365_lists() -> None:
    O365_DIR.mkdir(parents=True, exist_ok=True)

    client_request_id, latest_version = load_o365_version_state()
    version = o365_api_get("version", client_request_id)
    endpoint_sets = o365_api_get("endpoints", client_request_id)

    if version["latest"] > latest_version:
        print('New version of the "Office 365 worldwide commercial service instance endpoints" detected')
        write_o365_version_state(client_request_id, version["latest"])
    else:
        print("No new version detected, rewriting the existing lists for consistency.")

    grouped_ips: dict[str, set[IPAddressNetwork]] = defaultdict(set)
    urls: set[str] = set()

    for endpoint_set in endpoint_sets:
        if endpoint_set.get("category") not in O365_ALLOWED_CATEGORIES:
            continue

        tcp_ports = endpoint_set.get("tcpPorts", "")
        udp_ports = endpoint_set.get("udpPorts", "")
        file_name = ""

        if tcp_ports:
            file_name += f"tcp_{normalize_port_group(tcp_ports)}"
        if udp_ports:
            file_name += f"_udp_{normalize_port_group(udp_ports)}" if file_name else f"udp_{normalize_port_group(udp_ports)}"

        for ip_address in endpoint_set.get("ips", []):
            if file_name:
                grouped_ips[file_name].add(ipaddress.ip_network(ip_address, strict=False))

        urls.update(endpoint_set.get("urls", []))

    reset_o365_port_files()

    for file_name, networks in sorted(grouped_ips.items()):
        write_network_file(O365_DIR / f"{file_name}.txt", sorted(networks, key=sort_network_key))

    (O365_DIR / "url.txt").write_text("".join(f"{url}\n" for url in sorted(urls)), encoding="utf-8")
    print("Updated lists generated.")


def read_networks(file_path: Path) -> set[IPAddressNetwork]:
    networks: set[IPAddressNetwork] = set()
    if not file_path.exists():
        return networks

    for line in file_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            networks.add(ipaddress.ip_network(line, strict=False))
    return networks


def collect_networks(directory: Path, pattern: str) -> set[IPAddressNetwork]:
    networks: set[IPAddressNetwork] = set()
    for file_path in directory.glob(pattern):
        networks.update(read_networks(file_path))
    return networks


def collapse_networks(networks: set[IPAddressNetwork], version: int) -> list[IPAddressNetwork]:
    filtered = [network for network in networks if network.version == version]
    return sorted(ipaddress.collapse_addresses(filtered), key=sort_network_key)


def generate_aggregate_lists() -> None:
    AGGREGATE_DIR.mkdir(parents=True, exist_ok=True)

    github_networks = read_networks(GITHUB_FILE)
    azure_networks = collect_networks(AZURE_DIR, "*.txt")
    o365_tcp_networks = collect_networks(O365_DIR, "tcp_*.txt")
    o365_udp_networks = collect_networks(O365_DIR, "udp_*.txt")
    o365_mixed_networks = collect_networks(O365_DIR, "*_udp_*.txt")

    all_networks = github_networks | azure_networks | o365_tcp_networks | o365_udp_networks | o365_mixed_networks
    tcp_networks = github_networks | azure_networks | o365_tcp_networks | o365_mixed_networks
    udp_networks = o365_udp_networks | o365_mixed_networks

    output_sets = {
        "all_ipv4.txt": collapse_networks(all_networks, 4),
        "all_ipv6.txt": collapse_networks(all_networks, 6),
        "tcp_ipv4.txt": collapse_networks(tcp_networks, 4),
        "tcp_ipv6.txt": collapse_networks(tcp_networks, 6),
        "udp_ipv4.txt": collapse_networks(udp_networks, 4),
        "udp_ipv6.txt": collapse_networks(udp_networks, 6),
    }

    for file_name, networks in output_sets.items():
        write_network_file(AGGREGATE_DIR / file_name, networks)


def generate_docs_index() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    GENERATED_FILE.write_text(f"{generated_at}\n", encoding="utf-8")

    sections = [
        ("GitHub", [GITHUB_FILE]),
        ("Aggregate Lists", iter_files(AGGREGATE_DIR)),
        ("Azure Service Tags", iter_files(AZURE_DIR)),
        ("Microsoft 365 Endpoints", iter_files(O365_DIR)),
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


def generate_all() -> None:
    generate_azure_lists()
    generate_github_list()
    generate_o365_lists()
    generate_aggregate_lists()
    generate_docs_index()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate vendor endpoint lists and derived aggregate outputs.")
    parser.add_argument(
        "command",
        choices=("azure", "github", "o365", "aggregate", "index", "all"),
        help="Generation scope to run.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    commands = {
        "azure": generate_azure_lists,
        "github": generate_github_list,
        "o365": generate_o365_lists,
        "aggregate": generate_aggregate_lists,
        "index": generate_docs_index,
        "all": generate_all,
    }
    commands[args.command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
