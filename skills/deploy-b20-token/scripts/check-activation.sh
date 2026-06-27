#!/usr/bin/env bash
# Check whether B20 ASSET/STABLECOIN are activated on a given network before deploying.
# Usage: check-activation.sh <rpc-url>
#
# Exits 0 and prints "true true" if both variants are activated.
# Exits 1 if either variant is not activated, or the registry isn't reachable.
set -euo pipefail

RPC_URL="${1:?Usage: check-activation.sh <rpc-url>}"
REGISTRY=0x8453000000000000000000000000000000000001

ASSET_FEATURE=$(base-cast keccak "base.b20_asset")
STABLECOIN_FEATURE=$(base-cast keccak "base.b20_stablecoin")

ASSET_ACTIVATED=$(base-cast call "$REGISTRY" "isActivated(bytes32)(bool)" "$ASSET_FEATURE" --rpc-url "$RPC_URL")
STABLECOIN_ACTIVATED=$(base-cast call "$REGISTRY" "isActivated(bytes32)(bool)" "$STABLECOIN_FEATURE" --rpc-url "$RPC_URL")

echo "ASSET activated:      $ASSET_ACTIVATED"
echo "STABLECOIN activated: $STABLECOIN_ACTIVATED"

if [ "$ASSET_ACTIVATED" = "true" ] && [ "$STABLECOIN_ACTIVATED" = "true" ]; then
  exit 0
fi
exit 1
