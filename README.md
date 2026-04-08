# Microsoft Service Endpoint Lists

[![Microsoft Services IP-Lists](https://github.com/lenmail/microsoft_ip_list/actions/workflows/create_ms_service_ip_lists.yml/badge.svg)](https://github.com/lenmail/microsoft_ip_list/actions/workflows/create_ms_service_ip_lists.yml)

This repository generates consumable IP and URL lists from official vendor sources for operational use in firewalls, proxies, ACLs, and change management processes.

The generated artifacts are published under `docs/` and exposed through GitHub Pages:

- Repository: <https://github.com/lenmail/microsoft_ip_list>
- GitHub Pages: <https://lenmail.github.io/microsoft_ip_list/>
- Generated list index: <https://lenmail.github.io/microsoft_ip_list/index.md>

## Data Sources

- Azure Service Tags for Public Cloud: <https://www.microsoft.com/en-us/download/details.aspx?id=56519>
- Microsoft 365 IP Address and URL Web Service: <https://learn.microsoft.com/en-us/microsoft-365/enterprise/microsoft-365-ip-web-service?view=o365-worldwide>
- Azure Service Tags Overview: <https://learn.microsoft.com/en-us/azure/virtual-network/service-tags-overview>
- GitHub Meta API for official GitHub network ranges: <https://api.github.com/meta>
- GitHub documentation for IP ranges: <https://docs.github.com/en/github/authenticating-to-github/about-githubs-ip-addresses>

The generated lists are grouped in the index into three source families:

- GitHub
- Aggregate Lists
- Azure Service Tags
- Microsoft 365 Endpoints

## Operating Model

- `generate_list_azure.sh` downloads the current Azure Service Tags JSON from the Microsoft Download Center and writes one file per service tag to `docs/azure/`.
- `generate_list_github.py` reads the official GitHub Meta API and generates `docs/github.txt`.
- `generate_list_o365.py` queries the Microsoft 365 web service and generates port-based IP lists plus the URL list under `docs/o365/`.
- `generate_aggregate_lists.py` builds firewall- and proxy-friendly aggregate lists under `docs/aggregate/` for IPv4, IPv6, TCP, and UDP consumption.
- `generate_docs_index.py` builds `docs/index.md` and writes the generation timestamp to `docs/generated.txt`.
- The GitHub Actions workflow runs the generation daily, on push, and on manual dispatch, and commits only when there are real content changes.

## Local Execution

Requirements:

- `bash`
- `curl`
- `jq`
- `python3`

From the repository root:

```bash
./generate_list_azure.sh
python3 ./generate_list_github.py
python3 ./generate_list_o365.py
python3 ./generate_aggregate_lists.py
python3 ./generate_docs_index.py
```

If you consume the generated outputs through a service or cron-based downstream process, the resulting files should always be versioned as build artifacts or Git commits and integrated into the firewall change workflow.

## Operational Notes

- According to Microsoft, Azure Service Tags are published weekly. A daily check is operationally safe and detects new releases early.
- GitHub states that `api.github.com/meta` does not cover every possible GitHub IP for every service. `docs/github.txt` therefore intentionally aggregates the official GitHub Meta source, not a derived Azure helper list.
- The Microsoft 365 web service provides versioned endpoint data. The script rewrites the lists on every run for consistency, but only updates the stored version state when Microsoft publishes a newer version.
- The lists are deliberately split by service tag and port group so downstream systems can consume them selectively.
- The aggregate lists are intended for downstream automation such as firewall or proxy allowlists. `all_*` combines all known ranges, `tcp_*` combines protocol-agnostic sources plus Microsoft 365 TCP ranges, and `udp_*` only includes sources with explicit UDP semantics from Microsoft 365.
- For security-sensitive allowlisting, IP lists should never be treated in isolation. Microsoft recommends using service tags where possible for Azure and using URLs, ports, and a managed change process for Microsoft 365. For GitHub, the Meta API is the official reference point, but not a substitute for a service-level review.
