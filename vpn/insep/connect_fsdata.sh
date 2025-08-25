#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
else
  echo "Missing .env at $ENV_FILE" >&2
  exit 1
fi

SSH_USER=${SSH_USER:-${FS_DATA_USER:-}}
BASTION_HOST=${BASTION_HOST:-}
TARGET_HOST=${FS_DATA_HOST:-}

if [[ -z "$SSH_USER" || -z "$BASTION_HOST" || -z "$TARGET_HOST" ]]; then
  echo "Required variables missing. Ensure SSH_USER (or FS_DATA_USER), BASTION_HOST, FS_DATA_HOST are set in .env" >&2
  exit 1
fi

if ! ip link show tun0 >/dev/null 2>&1; then
  echo "Warning: VPN tun0 interface not found. Connect VPN first: $SCRIPT_DIR/connect_vpn.sh start" >&2
fi

# Prefer ProxyCommand with sshpass if a password is provided and sshpass exists
if [[ -n "${SSH_PASSWORD:-}" ]] && command -v sshpass >/dev/null 2>&1; then
  # Escape password for shell-safe embedding
  escaped_pw=$(printf %q "$SSH_PASSWORD")
  proxy_cmd="sshpass -p $escaped_pw ssh -o StrictHostKeyChecking=accept-new -W %h:%p -l \"$SSH_USER\" \"$BASTION_HOST\""
  exec sshpass -p "$SSH_PASSWORD" ssh \
    -o StrictHostKeyChecking=accept-new \
    -o ProxyCommand="$proxy_cmd" \
    -l "$SSH_USER" "$TARGET_HOST"
else
  # Fallback to ProxyJump; will prompt for passwords as needed
  exec ssh \
    -o StrictHostKeyChecking=accept-new \
    -J "$SSH_USER@$BASTION_HOST" \
    "$SSH_USER@$TARGET_HOST"
fi
