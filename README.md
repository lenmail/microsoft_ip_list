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

- `generate_lists.py` is the canonical entry point and contains the shared implementation for Azure, GitHub, Microsoft 365, aggregate lists, and the generated index.
- The GitHub Actions workflow runs the generation daily, on push, and on manual dispatch, and commits only when there are real content changes.

## Local Execution

Requirements:

- `python3`

From the repository root:

```bash
python3 ./generate_lists.py all
```

Individual scopes can still be generated separately:

```bash
python3 ./generate_lists.py azure
python3 ./generate_lists.py github
python3 ./generate_lists.py o365
python3 ./generate_lists.py aggregate
python3 ./generate_lists.py index
```

If you consume the generated outputs through a service or cron-based downstream process, the resulting files should always be versioned as build artifacts or Git commits and integrated into the firewall change workflow.

## Operational Notes

- According to Microsoft, Azure Service Tags are published weekly. A daily check is operationally safe and detects new releases early.
- GitHub states that `api.github.com/meta` does not cover every possible GitHub IP for every service. `docs/github.txt` therefore intentionally aggregates the official GitHub Meta source, not a derived Azure helper list.
- The Microsoft 365 web service provides versioned endpoint data. The script rewrites the lists on every run for consistency, but only updates the stored version state when Microsoft publishes a newer version.
- The lists are deliberately split by service tag and port group so downstream systems can consume them selectively.
- The aggregate lists are intended for downstream automation such as firewall or proxy allowlists. `all_*` combines all known ranges, `tcp_*` combines protocol-agnostic sources plus Microsoft 365 TCP ranges, and `udp_*` only includes sources with explicit UDP semantics from Microsoft 365. All aggregate outputs are CIDR-collapsed before they are written.
- For security-sensitive allowlisting, IP lists should never be treated in isolation. Microsoft recommends using service tags where possible for Azure and using URLs, ports, and a managed change process for Microsoft 365. For GitHub, the Meta API is the official reference point, but not a substitute for a service-level review.
