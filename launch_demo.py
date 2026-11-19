#!/usr/bin/env python3
"""Run Your Reflection on this laptop and refresh the gift card's LAN QR code."""

from __future__ import annotations

import argparse
import ipaddress
import re
import socket
import subprocess
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


PROJECT = Path(__file__).resolve().parent
SITE = PROJECT / "dist"
QR_IMAGE = SITE / "assets" / "your-reflection-qr.svg"
sys.path.insert(0, str(PROJECT / "vendor"))

import qrcode  # noqa: E402 - bundled for an offline, one-command launch
from qrcode.image.svg import SvgPathImage  # noqa: E402


def local_addresses() -> list[tuple[str, str]]:
    """Find IPv4 addresses without contacting an external service."""
    try:
        output = subprocess.run(
            ["ip", "-4", "-o", "addr", "show", "scope", "global"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    except OSError:
        output = ""

    found: list[tuple[str, str]] = []
    for line in output.splitlines():
        address = re.search(r"\binet\s+(\d+(?:\.\d+){3})/", line)
        if not address:
            continue
        interface = line.split(":", 2)[1].strip().split("@")[0]
        if interface.startswith(("docker", "veth", "virbr", "br-", "tun", "tap", "wg", "tailscale", "zt")):
            continue
        ip = address.group(1)
        if ipaddress.ip_address(ip).is_private:
            found.append((interface, ip))

    if found:
        found.sort(key=lambda item: (0 if item[0].startswith("wl") else 1 if item[0].startswith(("en", "eth")) else 2, item[0]))
        return found

    # A UDP connect chooses the laptop's local route but sends no packet.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.connect(("192.0.2.1", 80))
            ip = connection.getsockname()[0]
            if not ipaddress.ip_address(ip).is_loopback:
                return [("network", ip)]
    except OSError:
        pass
    return []


def make_qr(url: str) -> None:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
        image_factory=SvgPathImage,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr.make_image().save(QR_IMAGE)


class DemoHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Your Reflection on the local network.")
    parser.add_argument("--host", help="LAN IPv4 address or domain to show in the QR code (auto-detected by default)")
    parser.add_argument("--bind", help="IPv4 address to listen on (defaults to the selected LAN address)")
    parser.add_argument("--port", type=int, default=8765, help="HTTP port (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser tab automatically")
    parser.add_argument("--prepare-only", action="store_true", help="Update the QR code and exit")
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("the port must be between 1 and 65535")
    available = local_addresses()
    address = args.host or (available[0][1] if available else None)
    if address is None:
        parser.error("no local network address found; connect to Wi-Fi or pass --host YOUR_LAPTOP_IP")
    try:
        ipaddress.IPv4Address(address)
        host_is_ipv4 = True
    except ipaddress.AddressValueError:
        host_is_ipv4 = False
        if len(address) > 253 or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", address) or ".." in address:
            parser.error("--host must be an IPv4 address or a domain name")
    bind_address = args.bind or (address if host_is_ipv4 else "0.0.0.0")
    try:
        ipaddress.IPv4Address(bind_address)
    except ipaddress.AddressValueError:
        parser.error("--bind must be an IPv4 address on this machine")

    url = f"http://{address}:{args.port}/"
    make_qr(url)
    print(f"Gift card QR updated: {url}", flush=True)
    if args.prepare_only:
        return

    try:
        server = ThreadingHTTPServer((bind_address, args.port), partial(DemoHandler, directory=str(SITE)))
    except OSError as exc:
        parser.error(f"could not start on port {args.port}: {exc}")
    print(f"Gift card: http://{address}:{args.port}/gift-card.html", flush=True)
    print(f"Guests on the same network: {url}", flush=True)
    print("Press Ctrl+C to stop sharing.", flush=True)
    if not args.no_browser:
        webbrowser.open(f"http://{address}:{args.port}/gift-card.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDemo stopped.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
