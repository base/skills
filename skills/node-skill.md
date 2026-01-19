# Base Node Setup Guide

Help users run their own Base node for production environments.

## Why Run a Node

- Base's public RPCs are rate-limited and **not suitable for production apps**
- Running your own node provides reliable, unlimited access
- Required for high-throughput applications

## Hardware Requirements

**Minimum storage:** `(2 × chain_size) + snapshot_size + 20% buffer`

Account for snapshot restoration and chain data needs when provisioning storage.

## Networking Requirements

**Critical:** Port `9222` is critical for Reth peer discovery. If this port is blocked, your node may have difficulty finding peers and syncing.

- Ensure port 9222 (discv5) is open and accessible
- Configure firewall rules appropriately

## Syncing Considerations

**Syncing your node may take days and will consume a vast amount of your requests quota.**

- Monitor usage during initial sync
- Consider using snapshots to accelerate the process
- Upgrade your RPC plan if using external providers during sync

## Client Recommendations

**Important:** Geth Archive Nodes are no longer supported. For Archive functionality, use Reth, which provides significantly better performance in Base's high-throughput environment.

- Reth is recommended for Base nodes
- Provides better performance for high-throughput L2 environment
- Archive node support built-in

## Sync Status Verification

You'll know sync hasn't completed if you get `Error: nonce has already been used` when trying to deploy using your node.

Check sync status:
- Compare latest block with explorer
- Verify peer connections
- Monitor log output for sync progress

## Snapshots

Use node snapshots to accelerate initial sync:
- Check Base documentation for latest snapshot URLs
- Follow snapshot restoration procedures carefully
