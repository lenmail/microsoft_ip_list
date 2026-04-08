#!/usr/bin/env bash
set -euo pipefail

MICROSOFT_IP_RANGES_URL="https://www.microsoft.com/en-us/download/details.aspx?id=56519"
DOCS_DIR="docs/azure"
WORK_DIR="$(mktemp -d)"
JSON_FILE="${WORK_DIR}/service_tags.json"

cleanup() {
  rm -rf "${WORK_DIR}"
}

trap cleanup EXIT

mkdir -p "${DOCS_DIR}"

download_url="$(
  curl -fsSL "${MICROSOFT_IP_RANGES_URL}" \
    | grep -Eo 'https://download\.microsoft\.com/download/[^"]+ServiceTags_Public_[0-9]+\.json' \
    | head -n 1
)"

if [ -z "${download_url}" ]; then
  echo "Could not determine the current Azure Service Tags download URL." >&2
  exit 1
fi

curl -fsSL "${download_url}" -o "${JSON_FILE}"

jq -r '.values[] | select(.properties.region == "") | .name' "${JSON_FILE}" \
  | sort -u \
  | while IFS= read -r name; do
      output_file="${DOCS_DIR}/${name}.txt"
      tmp_output="${WORK_DIR}/${name}.txt"

      jq -r --arg name "${name}" '
        .values[]
        | select(.name == $name)
        | .properties.addressPrefixes[]
      ' "${JSON_FILE}" | sort -u > "${tmp_output}"

      if [ ! -s "${tmp_output}" ]; then
        echo "No address prefixes found for ${name}." >&2
        continue
      fi

      mv "${tmp_output}" "${output_file}"
    done
