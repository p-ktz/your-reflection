#!/usr/bin/env python3
"""Run Your Reflection locally or share it through a temporary public tunnel."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import io
import ipaddress
import os
import queue
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


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
    def __init__(self, *args, public_ready: threading.Event | None = None,
                 live_reload: bool = False, qr_svg: bytes | None = None, **kwargs) -> None:
        self.public_ready = public_ready
        self.live_reload = live_reload
        self.qr_svg = qr_svg
        super().__init__(*args, **kwargs)

    def _public_card_is_ready(self) -> bool:
        if self.public_ready is not None and not self.public_ready.is_set():
            path = urlsplit(self.path).path
            if path in ("/gift-card.html", "/assets/your-reflection-qr.svg"):
                self.send_error(503, "The public QR code is being prepared")
                return False
        return True

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
        if self._public_card_is_ready():
            if self.live_reload and self._serve_live_resource(head_only=False):
                return
            super().do_GET()

    def do_HEAD(self) -> None:
        if self._public_card_is_ready():
            if self.live_reload and self._serve_live_resource(head_only=True):
                return
            super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def run_public_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.public_provider == "localhost-run":
        run_localhost_run_demo(args, parser)
        return

    cloudflared = shutil.which("cloudflared")
    if cloudflared is None:
        parser.error(
            "cloudflared is required for --public; install it or use "
            "'docker compose -f compose.public.yaml up --build'"
        )

    bind_address = args.bind or "127.0.0.1"
    try:
        ipaddress.IPv4Address(bind_address)
    except ipaddress.AddressValueError:
        parser.error("--bind must be an IPv4 address on this machine")

    ready = threading.Event()
    try:
        server = ThreadingHTTPServer(
            (bind_address, args.port),
            partial(DemoHandler, directory=str(SITE), public_ready=ready),
        )
    except OSError as exc:
        parser.error(f"could not start on port {args.port}: {exc}")

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    origin_host = "127.0.0.1" if bind_address == "0.0.0.0" else bind_address
    command = [
        cloudflared,
        "tunnel",
        "--no-autoupdate",
        "--protocol",
        args.tunnel_protocol,
        "--url",
        f"http://{origin_host}:{args.port}",
    ]
    print("Starting a temporary public HTTPS tunnel...", flush=True)
    tunnel = None
    try:
        tunnel = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output: queue.Queue[str | None] = queue.Queue()

        def read_tunnel_output() -> None:
            assert tunnel is not None and tunnel.stdout is not None
            for line in tunnel.stdout:
                output.put(line.rstrip())
            output.put(None)

        threading.Thread(target=read_tunnel_output, daemon=True).start()
        public_url = None
        connected = False
        banner_seen = False
        deadline = time.monotonic() + 75
        while not (public_url and connected) and time.monotonic() < deadline:
            try:
                line = output.get(timeout=0.5)
            except queue.Empty:
                if tunnel.poll() is not None:
                    break
                continue
            if line is None:
                break
            print(f"[cloudflared] {line}", flush=True)
            if "your quick tunnel has been created" in line.lower():
                banner_seen = True
            if banner_seen and public_url is None:
                match = re.search(r"https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com/?", line, re.IGNORECASE)
                if match:
                    public_url = match.group(0).rstrip("/") + "/"
            if "registered tunnel connection" in line.lower():
                connected = True

        if public_url is None or not connected:
            raise RuntimeError(
                "The public tunnel did not become ready. Check internet access "
                "and the cloudflared messages above."
            )

        make_qr(public_url)
        ready.set()
        print(f"Public site: {public_url}", flush=True)
        print(f"Public gift card: {public_url}gift-card.html", flush=True)
        print(f"Public QR image: {public_url}assets/your-reflection-qr.svg", flush=True)
        print(f"Local gift card: http://{origin_host}:{args.port}/gift-card.html", flush=True)
        print("Share the public gift card or its QR; press Ctrl+C to stop.", flush=True)
        if not args.no_browser:
            webbrowser.open(f"http://{origin_host}:{args.port}/gift-card.html")

        while tunnel.poll() is None:
            try:
                line = output.get(timeout=0.5)
            except queue.Empty:
                continue
            if line is not None:
                print(f"[cloudflared] {line}", flush=True)
        raise RuntimeError("The public tunnel stopped; its QR link is no longer available.")
    except KeyboardInterrupt:
        print("\nPublic demo stopped.", flush=True)
    except RuntimeError as exc:
        parser.exit(1, f"Public demo error: {exc}\n")
    finally:
        ready.clear()
        if tunnel is not None and tunnel.poll() is None:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.kill()
                tunnel.wait(timeout=5)
        server.shutdown()
        server.server_close()


LOCALHOST_RUN_HOST = "localhost.run"
LOCALHOST_RUN_ED25519_FINGERPRINT = "SHA256:pG6qrBxubYfWa1Zadu/V0NUgjEDiBds/7e2xzte/QNM"
LOCALHOST_RUN_URL = re.compile(r"https://[a-z0-9-]+\.app\.lhr\.life/?(?![a-z0-9.-])", re.IGNORECASE)


def verified_localhost_run_host_key(path: Path) -> None:
    """Pin the official SSH key before letting SSH forward any requests."""
    try:
        result = subprocess.run(
            ["ssh-keyscan", "-T", "10", "-t", "ed25519", LOCALHOST_RUN_HOST],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Could not retrieve the localhost.run SSH host key: {exc}") from exc

    verified_lines = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) < 3 or fields[0] != LOCALHOST_RUN_HOST or fields[1] != "ssh-ed25519":
            continue
        try:
            key = base64.b64decode(fields[2], validate=True)
        except (ValueError, binascii.Error):
            continue
        fingerprint = "SHA256:" + base64.b64encode(hashlib.sha256(key).digest()).decode().rstrip("=")
        if fingerprint == LOCALHOST_RUN_ED25519_FINGERPRINT:
            verified_lines.append(" ".join(fields[:3]))

    if not verified_lines:
        raise RuntimeError(
            "localhost.run's SSH host key does not match its published fingerprint; "
            "refusing to create a tunnel."
        )
    path.write_text("\n".join(verified_lines) + "\n", encoding="ascii")
    path.chmod(0o600)


def public_site_is_healthy(url: str) -> bool:
    """Require the real demo page over HTTPS before publishing a QR to it."""
    try:
        request = Request(url, headers={"User-Agent": "YourReflectionDemo/1.0"})
        with urlopen(request, timeout=8) as response:
            return (
                response.status == 200
                and urlsplit(response.geturl()).hostname == urlsplit(url).hostname
                and b"Your Reflection" in response.read(128 * 1024)
            )
    except (HTTPError, URLError, TimeoutError, OSError):
        return False


def run_localhost_run_demo(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    ssh = shutil.which("ssh")
    keyscan = shutil.which("ssh-keyscan")
    if ssh is None or keyscan is None:
        parser.error(
            "OpenSSH client and ssh-keyscan are required for --public-provider localhost-run; "
            "use 'docker compose -f compose.localhostrun.yaml up --build'"
        )

    bind_address = args.bind or "127.0.0.1"
    try:
        ipaddress.IPv4Address(bind_address)
    except ipaddress.AddressValueError:
        parser.error("--bind must be an IPv4 address on this machine")

    ready = threading.Event()
    try:
        server = ThreadingHTTPServer(
            (bind_address, args.port),
            partial(DemoHandler, directory=str(SITE), public_ready=ready),
        )
    except OSError as exc:
        parser.error(f"could not start on port {args.port}: {exc}")

    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin_host = "127.0.0.1" if bind_address == "0.0.0.0" else bind_address
    tunnel = None
    try:
        with tempfile.TemporaryDirectory(prefix="your-reflection-ssh-") as key_dir:
            known_hosts = Path(key_dir) / "known_hosts"
            verified_localhost_run_host_key(known_hosts)
            command = [
                ssh,
                "-T",
                "-o", "BatchMode=yes",
                "-o", "ExitOnForwardFailure=yes",
                "-o", "ServerAliveInterval=15",
                "-o", "ServerAliveCountMax=2",
                "-o", "StrictHostKeyChecking=yes",
                "-o", f"UserKnownHostsFile={known_hosts}",
                "-o", "GlobalKnownHostsFile=/dev/null",
                "-o", "HostKeyAlgorithms=ssh-ed25519",
                "-R", f"80:{origin_host}:{args.port}",
                "nokey@localhost.run",
            ]
            print("Starting a temporary localhost.run HTTPS tunnel...", flush=True)
            tunnel = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            output: queue.Queue[str | None] = queue.Queue()

            def read_tunnel_output() -> None:
                assert tunnel is not None and tunnel.stdout is not None
                for line in tunnel.stdout:
                    output.put(line.rstrip())
                output.put(None)

            threading.Thread(target=read_tunnel_output, daemon=True).start()
            public_url = None
            deadline = time.monotonic() + 75
            while time.monotonic() < deadline:
                try:
                    line = output.get(timeout=0.5)
                except queue.Empty:
                    if tunnel.poll() is not None:
                        break
                    if public_url and public_site_is_healthy(public_url):
                        break
                    continue
                if line is None:
                    break
                # localhost.run prints a large ANSI QR in the terminal; the
                # gift card already contains the current QR once ready.
                if "\x1b[" not in line and "Open your tunnel address on your mobile with this QR" not in line:
                    print(f"[localhost.run] {line}", flush=True)
                if public_url is None:
                    match = LOCALHOST_RUN_URL.search(line)
                    if match:
                        public_url = match.group(0).rstrip("/") + "/"

            if public_url is None or tunnel.poll() is not None or not public_site_is_healthy(public_url):
                raise RuntimeError(
                    "The localhost.run link did not serve the demo successfully. "
                    "Check the tunnel messages above and try again."
                )

            make_qr(public_url)
            ready.set()
            print(f"Public site: {public_url}", flush=True)
            print(f"Public gift card: {public_url}gift-card.html", flush=True)
            print(f"Public QR image: {public_url}assets/your-reflection-qr.svg", flush=True)
            print(f"Local gift card: http://{origin_host}:{args.port}/gift-card.html", flush=True)
            print("Share the public gift card or its QR; press Ctrl+C to stop.", flush=True)
            if not args.no_browser:
                webbrowser.open(f"http://{origin_host}:{args.port}/gift-card.html")

            while tunnel.poll() is None:
                try:
                    line = output.get(timeout=0.5)
                except queue.Empty:
                    continue
                if line is not None:
                    print(f"[localhost.run] {line}", flush=True)
            raise RuntimeError("The public tunnel stopped; its QR link is no longer available.")
    except KeyboardInterrupt:
        print("\nPublic demo stopped.", flush=True)
    except RuntimeError as exc:
        parser.exit(1, f"Public demo error: {exc}\n")
    finally:
        ready.clear()
        if tunnel is not None and tunnel.poll() is None:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel.kill()
                tunnel.wait(timeout=5)
        server.shutdown()
        server.server_close()


def stop_on_sigterm(_signum: int, _frame: object) -> None:
    raise KeyboardInterrupt


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch Your Reflection locally or on a temporary public URL.")
    parser.add_argument("--public", action="store_true", help="Create a temporary worldwide HTTPS link")
    parser.add_argument("--public-provider", choices=("cloudflare", "localhost-run"), default="cloudflare",
                        help="Temporary tunnel provider for --public (default: cloudflare)")
    parser.add_argument("--tunnel-protocol", choices=("http2", "auto"), default="http2",
                        help="Cloudflare transport for --public (default: http2 for restricted networks)")
    parser.add_argument("--host", help="LAN IPv4 address or domain to show in the QR code (auto-detected by default)")
    parser.add_argument("--bind", help="IPv4 address to listen on (defaults to the selected LAN address)")
    parser.add_argument("--port", type=int, help="HTTP port (default: 8766 public, 8765 local)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser tab automatically")
    parser.add_argument("--prepare-only", action="store_true", help="Update the QR code and exit")
    parser.add_argument("--watch", action="store_true", help="Reload local browser pages after site files change")
    args = parser.parse_args()

    if args.port is None:
        args.port = 8766 if args.public else 8765
    if not 1 <= args.port <= 65535:
        parser.error("the port must be between 1 and 65535")
    signal.signal(signal.SIGTERM, stop_on_sigterm)
    if args.public_provider != "cloudflare" and not args.public:
        parser.error("--public-provider requires --public")
    if args.public:
        if args.watch:
            parser.error("--watch is only available for a local demo")
        if args.host or args.prepare_only:
            parser.error("--public cannot be combined with --host or --prepare-only")
        run_public_demo(args, parser)
        return
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
    qr_svg = render_qr(url) if args.watch and not args.prepare_only else None
    if qr_svg is None:
        make_qr(url)
        print(f"Gift card QR updated: {url}", flush=True)
    else:
        print(f"Gift card QR served: {url}", flush=True)
    if args.prepare_only:
        return

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
