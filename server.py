#!/usr/bin/env python3
"""Serve Your Reflection on a local network with an up-to-date gift card QR."""

from __future__ import annotations

import argparse
import hashlib
import io
import ipaddress
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


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


def render_qr(url: str) -> bytes:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
        image_factory=SvgPathImage,
    )
    qr.add_data(url)
    qr.make(fit=True)
    output = io.BytesIO()
    qr.make_image().save(output)
    return output.getvalue()


def make_qr(url: str) -> None:
    # Readers never see a partially written SVG while a tunnel starts.
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".your-reflection-qr-", suffix=".svg", dir=QR_IMAGE.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        temporary.write_bytes(render_qr(url))
        temporary.replace(QR_IMAGE)
    finally:
        temporary.unlink(missing_ok=True)


def site_version() -> str:
    """Change when any served site file changes, excluding the generated QR."""
    digest = hashlib.blake2s(digest_size=8)
    for path in sorted(SITE.rglob("*")):
        if not path.is_file() or path == QR_IMAGE or path.name.startswith(".your-reflection-qr-"):
            continue
        try:
            metadata = path.stat()
        except OSError:
            continue  # An editor may replace a file while we scan it.
        digest.update(f"{path.relative_to(SITE).as_posix()}:{metadata.st_mtime_ns}:{metadata.st_size}\n".encode())
    return digest.hexdigest()


LIVE_RELOAD_SCRIPT = """<script>
(() => {
  let version = "__SITE_VERSION__";
  let checking = false;
  async function checkForChanges() {
    if (checking) return;
    checking = true;
    try {
      const response = await fetch('/__dev/version', { cache: 'no-store' });
      if (!response.ok) return;
      const latest = (await response.text()).trim();
      if (latest !== version) { location.reload(); return; }
      version = latest;
    } catch (_) { /* The server may be restarting. */ }
    finally { checking = false; }
  }
  setInterval(checkForChanges, 800);
  document.addEventListener('visibilitychange', checkForChanges);
})();
</script>"""


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, live_reload: bool = False,
                 qr_svg: bytes | None = None, **kwargs) -> None:
        self.live_reload = live_reload
        self.qr_svg = qr_svg
        super().__init__(*args, **kwargs)

    def _send_live_content(self, content: bytes, content_type: str, head_only: bool) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def _serve_live_resource(self, head_only: bool) -> bool:
        path = urlsplit(self.path).path
        if path == "/__dev/version":
            self._send_live_content(site_version().encode(), "text/plain; charset=utf-8", head_only)
            return True
        if path == "/assets/your-reflection-qr.svg" and self.qr_svg is not None:
            self._send_live_content(self.qr_svg, "image/svg+xml", head_only)
            return True
        file_path = Path(self.translate_path(self.path))
        if file_path.is_dir():
            file_path /= "index.html"
        if file_path.suffix != ".html" or not file_path.is_file():
            return False
        try:
            source = file_path.read_bytes()
        except OSError:
            return False
        script = LIVE_RELOAD_SCRIPT.replace("__SITE_VERSION__", site_version()).encode()
        content = source.replace(b"</body>", script + b"\n</body>", 1)
        self._send_live_content(content, "text/html; charset=utf-8", head_only)
        return True

    def do_GET(self) -> None:
        if self.live_reload and self._serve_live_resource(head_only=False):
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if self.live_reload and self._serve_live_resource(head_only=True):
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def stop_on_sigterm(_signum: int, _frame: object) -> None:
    raise KeyboardInterrupt


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Your Reflection on a local network.")
    parser.add_argument("--host", help="LAN IPv4 address or domain to show in the QR code (auto-detected by default)")
    parser.add_argument("--bind", help="IPv4 address to listen on (defaults to the selected LAN address)")
    parser.add_argument("--port", type=int, default=8765, help="HTTP port (default: 8765)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser tab automatically")
    parser.add_argument("--watch", action="store_true", help="Reload browser pages after site files change")
    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("the port must be between 1 and 65535")
    signal.signal(signal.SIGTERM, stop_on_sigterm)
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
    qr_svg = render_qr(url) if args.watch else None
    if qr_svg is None:
        make_qr(url)
        print(f"Gift card QR updated: {url}", flush=True)
    else:
        print(f"Gift card QR served: {url}", flush=True)

    try:
        server = ThreadingHTTPServer((bind_address, args.port), partial(DemoHandler, directory=str(SITE),
                                                              live_reload=args.watch, qr_svg=qr_svg))
    except OSError as exc:
        parser.error(f"could not start on port {args.port}: {exc}")
    print(f"Gift card: http://{address}:{args.port}/gift-card.html", flush=True)
    print(f"Guests on the same network: {url}", flush=True)
    if args.watch:
        print("Live reload is on: save a file in dist/ to refresh open pages automatically.", flush=True)
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
