#!/usr/bin/env bash
#
# setup-viem-8130.sh — one-shot installer for viem's EIP-8130 / ERC-8168 modules.
#
# The 8130 tooling is not on npm yet (upstream PR wevm/viem#5004 is still an
# open draft). Until it ships, this builds it from the fork branch the PR is
# opened from — chunter-cb/viem feat/eip-8130-production — and links the built
# package into your project. Every step here is fiddly enough that doing it by
# hand invites mistakes, so this script captures the whole dance:
#
#   clone the fork branch -> pnpm build -> npm install --install-links
#
# When PR #5004 merges and a viem release ships the modules, this whole script
# collapses to `npm install viem@latest` — the imports (viem/eip8130,
# viem/eip8168) and APIs are unchanged, so nothing else in your code moves.
#
# Usage:
#   scripts/setup-viem-8130.sh [APP_DIR] [BUILD_DIR]
#
#   APP_DIR    project to install viem into (default: current directory)
#   BUILD_DIR  where to clone+build the fork (default: <APP_DIR>/.viem-8130-src)
#
# Env overrides:
#   VIEM_FORK_REPO    (default: https://github.com/chunter-cb/viem)
#   VIEM_FORK_BRANCH  (default: feat/eip-8130-production)
#
# Idempotent: re-running pulls the latest branch commit and rebuilds.

set -euo pipefail

APP_DIR="${1:-$PWD}"
APP_DIR="$(cd "$APP_DIR" && pwd)"                     # absolute
BUILD_DIR="${2:-$APP_DIR/.viem-8130-src}"
REPO="${VIEM_FORK_REPO:-https://github.com/chunter-cb/viem}"
BRANCH="${VIEM_FORK_BRANCH:-feat/eip-8130-production}"

echo "==> viem 8130 setup"
echo "    app:    $APP_DIR"
echo "    build:  $BUILD_DIR"
echo "    source: $REPO @ $BRANCH"

command -v git >/dev/null || { echo "error: git not found" >&2; exit 1; }
command -v npx >/dev/null || { echo "error: npx (Node.js) not found" >&2; exit 1; }

# 1) Clone or update the fork branch.
if [ -d "$BUILD_DIR/.git" ]; then
  echo "==> updating existing checkout"
  git -C "$BUILD_DIR" fetch origin "$BRANCH" --depth 1
  git -C "$BUILD_DIR" checkout "$BRANCH"
  git -C "$BUILD_DIR" reset --hard "origin/$BRANCH"
else
  echo "==> cloning $BRANCH"
  git clone -b "$BRANCH" --depth 1 "$REPO" "$BUILD_DIR"
fi

# 2) Build. --ignore-scripts skips the monorepo's postinstall hooks (which
#    aren't needed to produce the package and can fail in a bare checkout).
#    The build populates the package that lives in the repo's src/.
echo "==> installing build deps (pnpm, via npx — no global install)"
( cd "$BUILD_DIR" && npx --yes pnpm install --ignore-scripts )
echo "==> building viem"
( cd "$BUILD_DIR" && npx --yes pnpm run build )

# 3) Link into the app. --install-links is REQUIRED: without it npm symlinks
#    node_modules/viem to a path outside the project root, and bundlers
#    (Turbopack/Next.js) then fail with "Can't resolve 'viem'" even though tsc
#    resolves it fine — a confusing, wrong-looking bundler error.
echo "==> installing viem into the app (--install-links)"
( cd "$APP_DIR" && npm install --install-links "viem@file:$BUILD_DIR/src" )

cat <<EOF

==> done.
    Import 8130 helpers from 'viem/eip8130' and payer helpers from 'viem/eip8168'.
    Core helpers (createPublicClient, parseEther, ...) come from plain 'viem'.

    Set "target": "ES2020" (or later) in tsconfig.json — BigInt literals
    (0n) fail with TS2737 on any lower target, and create-next-app still
    generates "target": "ES2017".
EOF
