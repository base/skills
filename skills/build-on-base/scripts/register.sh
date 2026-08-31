#!/usr/bin/env bash
# Register an agent wallet with the Base builder code API.
# Usage: register.sh <wallet_address>
#
# On success, prints the builder_code value to stdout.
# On failure, prints the error to stderr and exits non-zero.

set -euo pipefail

WALLET_ADDRESS="${1:?Usage: register.sh <wallet_address>}"
API_URL="https://api.base.dev/v1/agents/builder-codes"

RESPONSE=$(curl -sf -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "{\"wallet_address\": \"$WALLET_ADDRESS\"}" 2>&1) || {
  echo "Error: API call to $API_URL failed" >&2
  echo "Response: $RESPONSE" >&2
  exit 1
}

# Match one or more spaces or tabs after the colon (pretty-printers may use either).
# Fall back to an empty value when the grep pipeline finds nothing, otherwise
# `set -euo pipefail` aborts the script here and the check below never runs.
BUILDER_CODE=$(echo "$RESPONSE" | grep -oE '"builder_code":[[:space:]]*"[^"]*"' | grep -oE '"[^"]*"$' | tr -d '"') || BUILDER_CODE=""

if [ -z "$BUILDER_CODE" ]; then
  echo "Error: No builder_code in API response" >&2
  echo "Response: $RESPONSE" >&2
  exit 1
fi

echo "$BUILDER_CODE"
