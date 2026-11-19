#!/usr/bin/env bash
set -euo pipefail

platform="${1:-}"
shift || true
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<EOF
Usage: ./start-${platform}.sh [--ip YOUR_LAN_IP]

Starts the local Docker demo and prints its site and QR-card addresses.
Use --ip only if automatic network detection selects the wrong adapter.
EOF
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

case "$platform" in
  linux) [[ "$(uname -s)" == Linux ]] || die 'Use start-linux.sh on Linux.' ;;
  macos) [[ "$(uname -s)" == Darwin ]] || die 'Use start-macos.sh on macOS.' ;;
  *) die 'Unsupported platform.' ;;
esac

override_ip=''
while (($#)); do
  case "$1" in
    --ip)
      (($# >= 2)) || die '--ip needs an IPv4 address.'
      override_ip="$2"
      shift 2
      ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; die "Unknown option: $1" ;;
  esac
done

valid_ipv4() {
  local address="$1" octet
  local -a parts
  [[ "$address" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || return 1
  IFS=. read -r -a parts <<< "$address"
  for octet in "${parts[@]}"; do
    [[ "$octet" == 0 || "$octet" != 0* ]] || return 1
    ((10#$octet <= 255)) || return 1
  done
  ((10#${parts[0]} > 0 && 10#${parts[0]} < 224)) || return 1
  ((10#${parts[0]} != 127)) || return 1
  ((10#${parts[0]} != 169 || 10#${parts[1]} != 254))
}

physical_interface() {
  case "$1" in
    lo|lo[0-9]*|docker*|veth*|virbr*|br-*|tun*|tap*|utun*|wg*|tailscale*|zt*|vboxnet*|vmnet*|podman*|cni*) return 1 ;;
    *) return 0 ;;
  esac
}

selected_ip=''
selected_interface=''
selected_score=99
route_interface=''

offer_address() {
  local interface="$1" address="$2" score=3
  physical_interface "$interface" || return 0
  valid_ipv4 "$address" || return 0
  case "$interface" in
    wl*|wlan*) score=1 ;;
    en*|eth*) score=2 ;;
  esac
  [[ "$interface" != "$route_interface" ]] || score=0
  if ((score < selected_score)); then
    selected_ip="$address"
    selected_interface="$interface"
    selected_score="$score"
  fi
}

if [[ -n "$override_ip" ]]; then
  valid_ipv4 "$override_ip" || die "Invalid LAN IPv4 address: $override_ip"
fi
command -v docker >/dev/null 2>&1 || die 'Docker is not installed. Install Docker Desktop or Docker Engine with Compose.'
docker compose version >/dev/null 2>&1 || die 'Docker Compose is unavailable. Install or update Docker with the Compose plugin.'
docker info --format '{{.ServerVersion}}' >/dev/null 2>&1 || die 'Docker Engine is not running or this user cannot access it. Start Docker and check Docker permissions.'
[[ -f "$project_dir/compose.yaml" && -f "$project_dir/Dockerfile" && -f "$project_dir/server.py" && -d "$project_dir/dist" && -d "$project_dir/vendor" ]] || die 'Project files are missing. Run the launcher from a complete copy of Your Reflection.'

if [[ -n "$override_ip" ]]; then
  selected_ip="$override_ip"
  selected_interface='manual'
elif [[ "$platform" == linux ]]; then
  if command -v ip >/dev/null 2>&1; then
    route_interface="$(ip -4 route get 192.0.2.1 2>/dev/null | awk '{for (i=1; i<=NF; i++) if ($i=="dev") {print $(i+1); exit}}' || true)"
    while IFS= read -r line; do
      read -r _ interface _ cidr _ <<< "$line"
      interface="${interface%%@*}"
      offer_address "$interface" "${cidr%%/*}"
    done < <(ip -4 -o addr show scope global 2>/dev/null || true)
  fi
  if [[ -z "$selected_ip" ]] && command -v hostname >/dev/null 2>&1; then
    for address in $(hostname -I 2>/dev/null || true); do
      if valid_ipv4 "$address"; then
        selected_ip="$address"
        selected_interface='network'
        break
      fi
    done
  fi
else
  if command -v route >/dev/null 2>&1; then
    route_interface="$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}' || true)"
  fi
  if command -v ifconfig >/dev/null 2>&1 && command -v ipconfig >/dev/null 2>&1; then
    for interface in $(ifconfig -l 2>/dev/null || true); do
      case "$interface" in en*|eth*) ;;
        *) continue ;;
      esac
      address="$(ipconfig getifaddr "$interface" 2>/dev/null || true)"
      offer_address "$interface" "$address"
    done
  fi
fi

[[ -n "$selected_ip" ]] || die 'No usable LAN IPv4 address found. Connect to Wi-Fi or run again with --ip YOUR_LAN_IP.'

cd "$project_dir"
export PUBLIC_HOST="$selected_ip"
printf 'Using %s (%s). Starting Your Reflection...\n' "$selected_ip" "$selected_interface"
docker compose up --build -d || die 'Docker could not start the demo. Check the error above; port 8765 may already be in use.'

ready=0
for ((attempt=0; attempt<30; attempt++)); do
  if command -v curl >/dev/null 2>&1; then
    if curl --silent --show-error --fail --max-time 2 --output /dev/null 'http://127.0.0.1:8765/gift-card.html' 2>/dev/null; then ready=1; break; fi
  elif docker compose exec -T your-reflection python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8765/gift-card.html', timeout=2).close()" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if ((ready == 0)); then
  docker compose logs --tail=40 your-reflection >&2 || true
  die 'The demo did not become ready at http://127.0.0.1:8765/gift-card.html.'
fi

printf '\nYour Reflection is ready.\n'
printf 'Site:      http://%s:8765/\n' "$selected_ip"
printf 'Gift card: http://%s:8765/gift-card.html\n' "$selected_ip"
printf 'Demo code: 271846\n'
printf 'Keep this computer on. Phones must join the same Wi-Fi or LAN.\n'
printf 'To stop: docker compose down (from this folder).\n'
