#!/usr/bin/env bash
set -euo pipefail

FILE=${1:-}
if [ -z "$FILE" ]; then
  echo "Usage: $0 <file-to-scan>" >&2
  echo "Example: $0 inputs.py" >&2
  exit 2
fi

python -m tests.scan_vulns "$FILE"
exit $?
