#!/usr/bin/env python3

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


WEB_SERVICE = "https://endpoints.office.com"
INSTANCE = "Worldwide"
DATA_PATH = Path("docs/o365")
VERSION_FILE = DATA_PATH / "endpoints_clientid_latestversion.txt"
ALLOWED_CATEGORIES = {"Optimize", "Allow"}


def web_api_get(method_name: str, instance_name: str, client_request_id: str) -> object:
    query = urlencode({"clientRequestId": client_request_id})
    request = Request(f"{WEB_SERVICE}/{method_name}/{instance_name}?{query}")
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def load_version_state() -> tuple[str, str]:
    if VERSION_FILE.exists():
        lines = VERSION_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) >= 2 and lines[0] and lines[1]:
            return lines[0], lines[1]

    client_request_id = str(uuid.uuid4())
    latest_version = "0000000000"
    VERSION_FILE.write_text(f"{client_request_id}\n{latest_version}\n", encoding="utf-8")
    return client_request_id, latest_version


def write_version_state(client_request_id: str, latest_version: str) -> None:
    VERSION_FILE.write_text(f"{client_request_id}\n{latest_version}\n", encoding="utf-8")


def reset_port_files() -> None:
    for pattern in ("tcp_*.txt", "udp_*.txt", "*udp_*.txt"):
        for file_path in DATA_PATH.glob(pattern):
            file_path.unlink()


def normalize_port_group(ports: str) -> str:
    return "_".join(part.strip() for part in ports.split(",") if part.strip())


def write_ip_lists(endpoint_sets: list[dict]) -> None:
    grouped_ips: dict[str, set[str]] = defaultdict(set)

    for endpoint_set in endpoint_sets:
        if endpoint_set.get("category") not in ALLOWED_CATEGORIES:
            continue

        tcp_ports = endpoint_set.get("tcpPorts", "")
        udp_ports = endpoint_set.get("udpPorts", "")
        file_name = ""

        if tcp_ports:
            file_name += f"tcp_{normalize_port_group(tcp_ports)}"
        if udp_ports:
            file_name += f"_udp_{normalize_port_group(udp_ports)}" if file_name else f"udp_{normalize_port_group(udp_ports)}"
        if not file_name:
            continue

        for ip_address in endpoint_set.get("ips", []):
            grouped_ips[file_name].add(ip_address)

    reset_port_files()

    for file_name, addresses in sorted(grouped_ips.items()):
        output_file = DATA_PATH / f"{file_name}.txt"
        output_file.write_text(
            "".join(f"{address}\n" for address in sorted(addresses)),
            encoding="utf-8",
        )


def write_url_list(endpoint_sets: list[dict]) -> None:
    urls = sorted(
        {
            url
            for endpoint_set in endpoint_sets
            if endpoint_set.get("category") in ALLOWED_CATEGORIES
            for url in endpoint_set.get("urls", [])
        }
    )
    (DATA_PATH / "url.txt").write_text(
        "".join(f"{url}\n" for url in urls),
        encoding="utf-8",
    )


def main() -> None:
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    client_request_id, latest_version = load_version_state()
    version = web_api_get("version", INSTANCE, client_request_id)
    endpoint_sets = web_api_get("endpoints", INSTANCE, client_request_id)

    if version["latest"] > latest_version:
        print('Neue Version der "Office 365 worldwide commercial service instance endpoints" gefunden')
        write_version_state(client_request_id, version["latest"])
    else:
        print("Keine neue Version gefunden, vorhandene Listen werden neu geschrieben.")

    write_ip_lists(endpoint_sets)
    write_url_list(endpoint_sets)

    print("Neue Listen erzeugt!")


if __name__ == "__main__":
    main()
