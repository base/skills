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

BUILDER_CODE=$(echo "$RESPONSE" | grep -o '"builder_code":"[^"]*"' | cut -d'"' -f4)

if [ -z "$BUILDER_CODE" ]; then
  echo "Error: No builder_code in API response" >&2
  echo "Response: $RESPONSE" >&2
  exit 1
fi

echo "$BUILDER_CODE"
