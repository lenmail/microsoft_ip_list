# Microsoft Service Endpoint Lists

[![Microsoft Services IP-Lists](https://github.com/lenmail/microsoft_ip_list/actions/workflows/create_ms_service_ip_lists.yml/badge.svg)](https://github.com/lenmail/microsoft_ip_list/actions/workflows/create_ms_service_ip_lists.yml)

Dieses Repository erzeugt aus offiziellen Herstellerquellen verwertbare IP- und URL-Listen fuer den operativen Einsatz in Firewalls, Proxys, ACLs und Change-Prozessen.

Die generierten Artefakte liegen unter `docs/` und werden ueber GitHub Pages veroeffentlicht:

- Repository: <https://github.com/lenmail/microsoft_ip_list>
- GitHub Pages: <https://lenmail.github.io/microsoft_ip_list/>
- Index der generierten Listen: <https://lenmail.github.io/microsoft_ip_list/index.md>

## Datenquellen

- Azure Service Tags fuer Public Cloud: <https://www.microsoft.com/en-us/download/details.aspx?id=56519>
- Microsoft 365 IP Address and URL Web Service: <https://learn.microsoft.com/en-us/microsoft-365/enterprise/microsoft-365-ip-web-service?view=o365-worldwide>
- Azure Service Tags Overview: <https://learn.microsoft.com/en-us/azure/virtual-network/service-tags-overview>
- GitHub Meta API fuer offizielle GitHub-Netzbereiche: <https://api.github.com/meta>
- GitHub Dokumentation zu IP-Adressen: <https://docs.github.com/en/github/authenticating-to-github/about-githubs-ip-addresses>

Die erzeugten Listen sind im Index in drei Quellfamilien gegliedert:

- GitHub
- Azure Service Tags
- Microsoft 365 Endpoints

## Betriebsmodell

- `generate_list_azure.sh` zieht die aktuelle Azure-Service-Tags-JSON aus dem Microsoft Download Center und schreibt pro Service Tag eine eigene Datei nach `docs/azure/`.
- `generate_list_github.py` liest die offizielle GitHub-Meta-API aus und erzeugt daraus `docs/github.txt`.
- `generate_list_o365.py` fragt den Microsoft-365-Webservice ab und erzeugt portbasierte IP-Listen sowie die URL-Liste unter `docs/o365/`.
- `generate_docs_index.py` erstellt `docs/index.md` und den Zeitstempel in `docs/generated.txt`.
- Der GitHub Actions Workflow fuehrt die Generierung taeglich sowie bei Push und manueller Ausloesung aus und committed nur bei echten Aenderungen.

## Lokale Ausfuehrung

Voraussetzungen:

- `bash`
- `curl`
- `jq`
- `python3`

Aus dem Repo-Root:

```bash
./generate_list_azure.sh
python3 ./generate_list_github.py
python3 ./generate_list_o365.py
python3 ./generate_docs_index.py
```

Falls du die Ergebnisse anschliessend als Service oder per Cron uebernehmen willst, sollten die erzeugten Dateien immer als Build-Artefakt oder Git-Commit versioniert und in den Firewall-Change-Prozess eingebunden werden.

## Hinweise fuer Betrieb und Architektur

- Azure Service Tags werden laut Microsoft woechentlich veroeffentlicht. Eine taegliche Pruefung ist betrieblich unkritisch und erkennt neue Versionen frueh.
- GitHub weist darauf hin, dass `api.github.com/meta` nicht jede moegliche GitHub-IP fuer jeden Dienst vollstaendig abdeckt. Fuer `docs/github.txt` wird deshalb bewusst die offizielle GitHub-Meta-Quelle aggregiert, nicht eine abgeleitete Azure-Hilfsliste.
- Der Microsoft-365-Webservice liefert versionierte Endpoint-Daten. Das Skript schreibt nur dann neue Listen, wenn Microsoft eine neue Version publiziert hat.
- Die Listen sind bewusst nach Service Tag und Port-Gruppen aufgeteilt, damit Downstream-Systeme selektiv konsumieren koennen.
- Fuer sicherheitskritische Freigaben sollten IP-Listen nie isoliert betrachtet werden. Microsoft empfiehlt fuer Azure nach Moeglichkeit Service Tags und fuer Microsoft 365 die Kombination aus URLs, Ports und Change-Prozess. Fuer GitHub ist die Meta-API die offizielle Referenz, aber kein Ersatz fuer einen eigenen Review auf Dienstebene.
