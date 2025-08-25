#!/usr/bin/env bash
set -euo pipefail

# Location of repo and env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
else
  echo "Missing .env at $ENV_FILE" >&2
  exit 1
fi

if [[ -z "${VPN_OVPN:-}" ]]; then
  echo "VPN_OVPN is not set in .env" >&2
  exit 1
fi

cmd=${1:-connect}

ensure_openvpn_installed() {
  if ! command -v openvpn >/dev/null 2>&1; then
    echo "OpenVPN not found. Install it: sudo apt update && sudo apt install -y openvpn" >&2
    exit 1
  fi
}

vpn_pid_file="$SCRIPT_DIR/.openvpn.pid"

start_vpn() {
  ensure_openvpn_installed
  if [[ -f "$vpn_pid_file" ]] && kill -0 "$(cat "$vpn_pid_file")" 2>/dev/null; then
    echo "OpenVPN already running with PID $(cat "$vpn_pid_file")"
    return 0
  fi
  sudo -n true 2>/dev/null || echo "sudo may prompt for password to start OpenVPN..."
  # Run in background and capture PID
  sudo openvpn --config "$VPN_OVPN" --daemon
  # Best-effort: find the most recent openvpn pid
  sleep 1
  pgrep -x openvpn | tail -n1 > "$vpn_pid_file" || true
  echo "OpenVPN started. Checking interface..."
  for i in {1..20}; do
    if ip link show tun0 >/dev/null 2>&1; then
      echo "VPN up (tun0 present)."
      return 0
    fi
    sleep 1
  done
  echo "Warning: tun0 not detected; connection may still be initializing." >&2
}

stop_vpn() {
  if [[ -f "$vpn_pid_file" ]]; then
    if kill -0 "$(cat "$vpn_pid_file")" 2>/dev/null; then
      sudo kill "$(cat "$vpn_pid_file")" || true
      rm -f "$vpn_pid_file"
      echo "OpenVPN stopped."
      return 0
    fi
    rm -f "$vpn_pid_file"
  fi
  # Fallback: kill any openvpn owned by user via sudo
  if pgrep -x openvpn >/dev/null; then
    echo "Killing running openvpn processes..."
    sudo pkill -x openvpn || true
  fi
}

status_vpn() {
  if ip link show tun0 >/dev/null 2>&1; then
    echo "VPN interface tun0 is up."
    ip addr show tun0 | sed 's/^/  /'
  else
    echo "VPN interface tun0 is down."
  fi
  if pgrep -x openvpn >/dev/null; then
    echo "OpenVPN process running (PIDs): $(pgrep -x openvpn | xargs)"
  else
    echo "No openvpn process running."
  fi
}

case "$cmd" in
  connect|start)
    start_vpn
    ;;
  stop)
    stop_vpn
    ;;
  status)
    status_vpn
    ;;
  restart)
    stop_vpn
    start_vpn
    ;;
  *)
    echo "Usage: $0 {connect|start|stop|status|restart}" >&2
    exit 2
    ;;

esac
