#!/usr/bin/env bash
# register-erc8004.sh — Register an agent on ERC-8004 Identity Registry (Base)
# Usage: bash register-erc8004.sh <agent_uri> [--sepolia]
#
# Requires: cast (Foundry), PRIVATE_KEY env var
#
# Example:
#   export PRIVATE_KEY=0x...
#   AGENT_URI="data:application/json;base64,$(cat agent-registration.json | base64 -w0)"
#   bash register-erc8004.sh "$AGENT_URI"
#
# Output: agentId (uint256) on success

set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: bash register-erc8004.sh <agent_uri> [--sepolia]" >&2
  exit 1
fi

AGENT_URI="$1"
SEPOLIA="${2:-}"

if [ -z "${PRIVATE_KEY:-}" ]; then
  echo "Error: PRIVATE_KEY environment variable not set" >&2
  exit 1
fi

if [ "$SEPOLIA" = "--sepolia" ]; then
  REGISTRY="0x8004A818BFB912233c491871b3d84c89A494BD9e"
  RPC="https://sepolia.base.org"
  NETWORK="Base Sepolia"
else
  REGISTRY="0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
  RPC="https://mainnet.base.org"
  NETWORK="Base Mainnet"
fi

echo "Registering agent on $NETWORK..." >&2
echo "Registry: $REGISTRY" >&2

# Send registration tx
TX_OUTPUT=$(cast send "$REGISTRY" \
  "register(string)(uint256)" "$AGENT_URI" \
  --rpc-url "$RPC" \
  --private-key "$PRIVATE_KEY" 2>&1)

TX_HASH=$(echo "$TX_OUTPUT" | grep -oP 'transactionHash \K[0-9a-fx]+' || echo "")

if [ -z "$TX_HASH" ]; then
  echo "Error: Registration transaction failed" >&2
  echo "$TX_OUTPUT" >&2
  exit 1
fi

echo "Tx: $TX_HASH" >&2

# Get agentId from the Registered event
RECEIPT=$(cast receipt "$TX_HASH" --rpc-url "$RPC" 2>&1)

# Extract tokenId from the Registered event (topic 2 = agentId, indexed)
AGENT_ID=$(echo "$RECEIPT" | grep -oP 'topics.*?\n' | head -5 || echo "")

# Fallback: try to parse from logs
if [ -z "$AGENT_ID" ]; then
  # Try parsing event data
  AGENT_ID=$(cast receipt "$TX_HASH" --json --rpc-url "$RPC" 2>/dev/null | \
    python3 -c "
import json, sys
data = json.load(sys.stdin)
for log in data.get('logs', []):
    topics = log.get('topics', [])
    if len(topics) >= 2:
        # Registered event: first topic is event signature, second is agentId
        agent_id = int(topics[1], 16)
        if agent_id > 0:
            print(agent_id)
            break
" 2>/dev/null || echo "")
fi

if [ -n "$AGENT_ID" ]; then
  echo "$AGENT_ID"
  echo "✅ Registered! agentId: $AGENT_ID" >&2
else
  echo "Warning: Could not parse agentId from receipt. Check tx: $TX_HASH" >&2
  echo "$TX_HASH"
fi
