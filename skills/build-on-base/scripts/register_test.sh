#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

cat >"$TMP_DIR/curl" <<'FAKE_CURL'
#!/usr/bin/env bash
cat <<'JSON'
{
  "builder_code": "bc_a1b2c3d4",
  "wallet_address": "0x123",
  "usage_instructions": "Append this builder code to your onchain transactions."
}
JSON
FAKE_CURL
chmod +x "$TMP_DIR/curl"

set +e
output=$(PATH="$TMP_DIR:$PATH" bash "$SCRIPT_DIR/register.sh" "0x123" 2>&1)
status=$?
set -e

if [ "$status" -ne 0 ]; then
  echo "Expected register.sh to succeed, got exit $status:" >&2
  echo "$output" >&2
  exit 1
fi

if [ "$output" != "bc_a1b2c3d4" ]; then
  echo "Expected builder code bc_a1b2c3d4, got: $output" >&2
  exit 1
fi
