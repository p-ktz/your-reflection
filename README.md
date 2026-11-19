# Your Reflection

**A story in every pearl.** Your Reflection is a standalone, presentation-ready concept for a more personal jewelry gift experience. A recipient scans the card inside a gift box, enters a six-digit demo code, and explores memories hidden in three pearls on a bracelet.

> [!NOTE]
> This is an independent concept inspired by the [Van Cleef & Arpels Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html). It is not an official Van Cleef & Arpels website or product.

![Desktop view of Your Reflection showing the interactive gold bracelet and three memory pearls](docs/screenshots/bracelet.webp)

| Gift reveal | Access screen |
| --- | --- |
| ![Printable concept gift card with a QR code and six-digit demo code](docs/screenshots/gift-card.webp) | ![Your Reflection access screen asking for the code from the gift](docs/screenshots/access.webp) |

<img src="docs/screenshots/mobile.webp" alt="Mobile view of the bracelet experience with three glowing memory pearls" width="300">

The screenshots show an example QR. The launcher replaces it with the current network address before you share the card.

## The experience

1. A gift giver chooses memories to accompany a bracelet. This demo includes **two photos and one video** as sample memories.
2. The recipient finds a printed card with a QR code and six-digit code in the box.
3. Scanning the QR opens Your Reflection on the hosting laptop or server. The recipient enters **`271846`**.
4. Three glowing pearls on the bracelet reveal the memories. The recipient can continue through them, read a personal note, and follow a link to the [official Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html).

The gift giver's upload and purchase flow is a **concept only**; this repository implements the recipient experience and printable sample card.

### What is included

- Responsive desktop and mobile layouts, pearl hover/focus states, subtle motion, and a memory dialog.
- Keyboard navigation, touch swipe, visible focus, reduced-motion support, and captions for the video.
- A printable gift card whose QR is regenerated for the current address when the demo starts.
- A local network demo that runs on the hosting laptop, with optional public tunnel modes retained for reference. Fonts, media, and the QR generator are bundled; the site itself does not need an API or database.

## Run on the same Wi-Fi or LAN

This is the recommended presentation setup. Connect the hosting laptop and the recipient's phone to the **same Wi-Fi or LAN** (a laptop hotspot also works). Find the laptop's LAN IPv4 address, then run the following command from the project directory. Replace `192.168.1.23` with that address:

```bash
PUBLIC_HOST=192.168.1.23 docker compose up --build
```

On Windows PowerShell, set `$env:PUBLIC_HOST = "192.168.1.23"` and then run `docker compose up --build`. Docker with Compose is required; the first image build may need internet to download the Python base image. Keep the laptop awake and the command running during the presentation.

Open `http://YOUR_LAN_IP:8765/gift-card.html` on the laptop. The card contains the freshly generated QR, which opens `http://YOUR_LAN_IP:8765/`. Scan it from a phone on the same network and enter **`271846`**. Stop the demo with `Ctrl+C` or `docker compose down`. If the laptop's IP changes, restart the demo and share the new QR.

Without Docker, use `python3 launch_demo.py` (Windows: `py -3 launch_demo.py`). Python 3.10+ is required; no `pip install` is needed. The launcher detects the LAN IP and opens the card. On Linux/macOS, `./start-demo.sh` is another shortcut. If it selects the wrong network adapter, use `python3 launch_demo.py --host YOUR_LAN_IP`. Run `python3 launch_demo.py --help` for all options.

This address is reachable only from the same network. Guest Wi-Fi may block devices from reaching one another; if a phone cannot open the card, check network isolation and whether the laptop's firewall allows TCP port `8765`.

## Optional worldwide sharing with Docker

You need [Docker](https://docs.docker.com/get-docker/) with Compose and an internet connection. Download or clone this repository, open a terminal in its root directory, and run the same command on Linux, macOS, or Windows:

```console
docker compose -f compose.localhostrun.yaml up --build
```

Wait for the terminal to print **Public site**, **Public gift card**, and **Public QR image** URLs. Open the public gift card on your laptop, then send its QR image or a screenshot of the card to someone **anywhere with internet access**. They scan it and enter **`271846`**. The local card is also available at `http://127.0.0.1:8766/gift-card.html` on the hosting computer.

No account, domain, same-Wi-Fi connection, or inbound port forwarding is needed for this demo mode. The [localhost.run free tunnel](https://localhost.run/docs/forever-free) provides a temporary HTTPS address; its domain can change, and free traffic has a speed limit. Keep Docker and the host computer online during the presentation. Stop with `Ctrl+C` or `docker compose -f compose.localhostrun.yaml down`. Start it again and share its **new** QR if the address expires or the tunnel disconnects.

**Why a tunnel?** A QR only opens a URL; the laptop's local address cannot be reached from another network. A tunnel gives the demo a public address without router setup. For a real deployment, use a public server with a stable domain, HTTPS, and proper access control. Public demo traffic, including the sample photos and video, passes through the tunnel provider; [localhost.run terminates HTTPS](https://localhost.run/docs/http-tunnels).

### Cloudflare alternative

The original [Cloudflare Quick Tunnel](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) mode remains available:

```console
docker compose -f compose.public.yaml up --build
```

It uses the same local port and cannot run alongside the localhost.run Compose mode. [Quick Tunnels have no uptime guarantee](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/). If a QR opens **Cloudflare Error 1033**, the tunnel connector is unavailable: check the terminal logs, restart the tunnel, and share the newly generated QR. If the error persists, use the localhost.run mode or a public server. The QR and six-digit code cannot repair an unavailable tunnel.

## Optional worldwide sharing without Docker

You need **Python 3.10+**, a modern browser, and OpenSSH for localhost.run. No `pip install` is required. For the Cloudflare alternative, install [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/).

**Linux / macOS**

```bash
python3 launch_demo.py --public --public-provider localhost-run
```

**Windows PowerShell**

```powershell
py -3 launch_demo.py --public --public-provider localhost-run
```

The launcher starts a local server and tunnel, checks the public experience, then refreshes the QR. It prints the public URLs and opens the card on the host. Keep the terminal open; press `Ctrl+C` to stop. To use Cloudflare, omit `--public-provider localhost-run`.

## Presenting the demo

1. Start the local Docker or Python mode and wait for the LAN URLs to appear.
2. Open the gift card URL and select **Print this sample card** if you want a physical insert.
3. Give the recipient the current QR and code **`271846`**. Their phone must be on the same network as the laptop.
4. Have the recipient select each of the three glowing pearls, then follow the link to the official collection.

### Troubleshooting

| Problem | Check |
| --- | --- |
| The public URL does not appear | Check the host's internet connection and tunnel messages in the terminal. The optional localhost.run mode needs outbound SSH access; the Cloudflare mode needs outbound access to Cloudflare. |
| A sent QR stopped working | Temporary tunnel URLs can expire or change on restart. Start the demo again and send the newly generated QR or public gift card URL. |
| Cloudflare Error 1033 | Cloudflare cannot find a healthy tunnel connector. Confirm the host and container are running, inspect tunnel logs, then restart and share the new QR. If it persists, use the localhost.run mode or a public server. |
| The phone cannot open a local-only QR | Confirm both devices use the same network, the host is running, and TCP port `8765` is allowed by the host firewall. Guest Wi-Fi may isolate devices. |
| A demo port is in use | Local mode uses `8765`; public mode uses `8766`. Stop the process using that port or pass `--port` for native Python. For Docker, keep the container port, Compose mapping, and launcher `--port` value aligned; in local mode, the QR must show the host's reachable port. |
| Local Docker says `PUBLIC_HOST` is missing | Set that variable in the same terminal before running `docker compose up --build`. The optional public Compose files do not need it. |

## Project structure

```text
.
├── dist/                 Website, gift card, fonts, and sample media
│   ├── index.html        Recipient experience
│   ├── gift-card.html    Printable concept insert
│   └── assets/           Bracelet artwork, memories, captions, and QR
├── docs/screenshots/     README previews
├── launch_demo.py        Local HTTP server and QR generator
├── start-demo.sh         Linux/macOS launcher shortcut
├── Dockerfile            Container image
├── compose.yaml          Portable Docker run configuration
├── Dockerfile.public     Cloudflare tunnel image
├── Dockerfile.localhostrun  Cloudflare-free SSH tunnel image
├── compose.public.yaml   Cloudflare Quick Tunnel mode
├── compose.localhostrun.yaml  localhost.run tunnel mode
└── vendor/               Bundled QR library and license notices
```

The site is plain HTML, CSS, and JavaScript. Edit files in `dist/` to change the UI and copy. The three demo memories are configured in [`dist/app.js`](dist/app.js); their media files are in [`dist/assets/`](dist/assets/).

### Customize the demo

| Change | Where |
| --- | --- |
| Memory titles, messages, and media order | The `memories` array in [`dist/app.js`](dist/app.js) |
| Sample photos, video, poster, and captions | [`dist/assets/`](dist/assets/) |
| Six-digit demo code | `DEMO_CODE` in [`dist/app.js`](dist/app.js), the sample code displayed in [`dist/index.html`](dist/index.html), and the printed code in [`dist/gift-card.html`](dist/gift-card.html) |
| Colors, type, layout, and effects | [`dist/styles.css`](dist/styles.css) and [`dist/gift-card.css`](dist/gift-card.css) |

After changing files, restart the Python launcher or rebuild the Docker container. The launcher generates the QR automatically; do not hard-code a new address into the SVG.

## Demo scope, privacy, and publication

The six-digit code is a **visual demo step, not authentication**. In local mode, other devices on the same network can request the sample media files directly. In optional public mode, anyone with the temporary URL can request those files, and the tunnel provider can process the traffic. Use only media you are comfortable sharing this way. A production version would need purchase-linked authorization, private media storage, consent, retention rules, and secure delivery.

**Before publishing this repository publicly**, review the rights and consent for every image and video in `dist/assets/` and for any screenshots in `docs/screenshots/`; replace them if needed. The bracelet artwork is concept imagery, not an official product photograph. The card and website both link to the official collection, and both identify this as an independent demo.

## License and credits

No license has been selected for this project's original code or media. Public GitHub visibility alone does not grant reuse rights. The bundled QR library and fonts retain their own notices in [`vendor/`](vendor/). Confirm media rights and [choose a project license](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) before inviting reuse or contributions.
