#!/usr/bin/env bash
set -e
if [ -z "$1" ]; then
  echo "Usage: $0 <module_file>"
  exit 2
fi
MODULE=$1
python -u tests/test_runner.py --module "$MODULE"
exit $?
