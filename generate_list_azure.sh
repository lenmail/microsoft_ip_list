#!/usr/bin/env bash
set -euo pipefail

python3 "$(cd "$(dirname "$0")" && pwd)/generate_lists.py" azure
