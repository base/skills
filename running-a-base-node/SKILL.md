---
name: running-a-base-node
description: Runs a Base node for production environments. Covers hardware requirements, Reth client setup, networking, and sync troubleshooting. Use when setting up self-hosted RPC infrastructure or running archive nodes.
---

# Running a Base Node

For production apps requiring reliable, unlimited RPC access.

## Hardware Requirements

- **CPU**: 8-Core minimum
- **RAM**: 16 GB minimum
- **Storage**: NVMe SSD, formula: `(2 × chain_size) + snapshot_size + 20% buffer`

## Networking

**Required Ports:**
- **Port 9222**: Critical for Reth Discovery v5
- **Port 30303**: P2P Discovery & RLPx

If these ports are blocked, the node will have difficulty finding peers and syncing.

## Client Selection

Use **Reth** for Base nodes. Geth Archive Nodes are no longer supported.

Reth provides:
- Better performance for high-throughput L2
- Built-in archive node support

## Syncing

- Initial sync takes **days**
- Consumes significant RPC quota if using external providers
- Use snapshots to accelerate (check Base docs for URLs)

## Sync Status

**Incomplete sync indicator**: `Error: nonce has already been used` when deploying.

Verify sync:
- Compare latest block with explorer
- Check peer connections
- Monitor logs for progress
