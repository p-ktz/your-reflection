# Your Reflection

**A story in every pearl.** Your Reflection is a standalone, presentation-ready concept for a more personal jewelry gift experience. A recipient scans the card inside a gift box, enters a six-digit demo code, and explores memories hidden in three pearls on a bracelet.

> [!NOTE]
> This is an independent concept inspired by the [Van Cleef & Arpels Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html). It is not an official Van Cleef & Arpels website or product.

![Desktop view of Your Reflection showing the interactive gold bracelet and three memory pearls](docs/screenshots/bracelet.webp)

| Gift reveal | Access screen |
| --- | --- |
| ![Printable concept gift card with a QR code and six-digit demo code](docs/screenshots/gift-card.webp) | ![Your Reflection access screen asking for the code from the gift](docs/screenshots/access.webp) |

<img src="docs/screenshots/mobile.webp" alt="Mobile view of the bracelet experience with three glowing memory pearls" width="300">

The screenshots show an example QR. The launcher replaces it with the current public or local address before you share the card.

## The experience

1. A gift giver chooses memories to accompany a bracelet. This demo includes **two photos and one video** as sample memories.
2. The recipient finds a printed card with a QR code and six-digit code in the box.
3. Scanning the QR opens Your Reflection on the hosting laptop or server. The recipient enters **`271846`**.
4. Three glowing pearls on the bracelet reveal the memories. The recipient can continue through them, read a personal note, and follow a link to the [official Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html).

The gift giver's upload and purchase flow is a **concept only**; this repository implements the recipient experience and printable sample card.

### What is included

- Responsive desktop and mobile layouts, pearl hover/focus states, subtle motion, and a memory dialog.
- Keyboard navigation, touch swipe, visible focus, reduced-motion support, and captions for the video.
- A printable gift card whose QR is regenerated for the current public or local address when the demo starts.
- One-command public HTTPS sharing through a temporary [Cloudflare Quick Tunnel](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), plus a local-only mode. Fonts, media, and the QR generator are bundled; the site itself does not need an API or database.

## Share worldwide with Docker

You need [Docker](https://docs.docker.com/get-docker/) with Compose and an internet connection. Download or clone this repository, open a terminal in its root directory, and run the same command on Linux, macOS, or Windows:

```console
docker compose -f compose.public.yaml up --build
```

Wait for the terminal to print **Public site**, **Public gift card**, and **Public QR image** URLs. Open the public gift card on your laptop, then send its QR image or a screenshot of the card to someone **anywhere with internet access**. They scan it and enter **`271846`**. The local card is also available at `http://127.0.0.1:8766/gift-card.html` on the hosting computer.

No Cloudflare account, domain, same-Wi-Fi connection, or inbound port forwarding is needed for this demo mode. The public URL is temporary: it **changes on every start** and stops working when the tunnel or host stops. Keep Docker and the host computer online during the presentation. Stop with `Ctrl+C` or `docker compose -f compose.public.yaml down`; rebuild after editing with the command above.

**Why Cloudflare?** A QR only opens a URL; the laptop's local address cannot be reached from another network. Quick Tunnel gives this demo a temporary public URL without router setup. For a real deployment, use a public server with a stable domain, HTTPS, and proper access control; [Quick Tunnels have no uptime guarantee](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Share worldwide without Docker

You need **Python 3.10+**, a modern browser, and [`cloudflared` installed](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/). No `pip install` is required.

**Linux / macOS**

```bash
python3 launch_demo.py --public
```

**Windows PowerShell**

```powershell
py -3 launch_demo.py --public
```

The launcher starts a local server and a Cloudflare tunnel, waits for the public link to connect, then refreshes the QR. It prints the public URLs and opens the card on the host. Keep the terminal open; press `Ctrl+C` to stop.

## Local-only mode

For an offline or same-network presentation, use `python3 launch_demo.py` (Windows: `py -3 launch_demo.py`). The launcher detects a local IP address and generates a LAN QR. You can also run `./start-demo.sh` on Linux/macOS. If the wrong adapter is chosen, pass `--host 192.168.1.23` with your computer's LAN IP.

With Docker, the original local Compose setup remains available. Set `PUBLIC_HOST` to the host's reachable LAN IP:

```bash
PUBLIC_HOST=192.168.1.23 docker compose up --build
```

In Windows PowerShell, run `$env:PUBLIC_HOST = "192.168.1.23"` and then `docker compose up --build`. Replace the example IP with your own. Visitors must be on the **same Wi-Fi or LAN** as the host for this mode. To stop it, use `Ctrl+C` or `docker compose down`.

Run `python3 launch_demo.py --help` for the full launcher options. If the host address changes in either mode, restart and share the **new** QR. The SVG included in a checkout is only a sample.

## Presenting the demo

1. Start the **public** or **local-only** mode and wait for the URLs to appear.
2. Open the gift card URL and select **Print this sample card** if you want a physical insert.
3. Give or send the recipient the current QR and code **`271846`**. In public mode, they can be anywhere with internet access.
4. Have the recipient select each of the three glowing pearls, then follow the link to the official collection.

### Troubleshooting

| Problem | Check |
| --- | --- |
| The public URL does not appear | Check the host's internet connection and the `cloudflared` messages in the terminal. The public mode needs outbound access to Cloudflare. |
| A sent QR stopped working | Quick Tunnel URLs change on restart. Start the demo again and send the newly generated QR or public gift card URL. |
| The phone cannot open a local-only QR | Confirm both devices use the same network, the host is running, and TCP port `8765` is allowed by the host firewall. Guest Wi-Fi may isolate devices. |
| A demo port is in use | Local mode uses `8765`; public mode uses `8766`. Stop the process using that port or pass `--port` for native Python. For Docker, keep the container port, Compose mapping, and launcher `--port` value aligned; in local mode, the QR must show the host's reachable port. |
| Local Docker says `PUBLIC_HOST` is missing | Set that variable in the same terminal before running the **local** `docker compose up --build` command. The public Compose file does not need it. |

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
├── Dockerfile.public     Image with the Cloudflare tunnel client
├── compose.public.yaml   Worldwide demo via temporary HTTPS tunnel
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

The six-digit code is a **visual demo step, not authentication**. In public mode, the sample photos and video are served as ordinary static files to anyone who has the temporary URL or requests their asset paths. Use only media you are comfortable sharing through this tunnel. A production version would need purchase-linked authorization, private media storage, consent, retention rules, and secure delivery.

**Before publishing this repository publicly**, review the rights and consent for every image and video in `dist/assets/` and for any screenshots in `docs/screenshots/`; replace them if needed. The bracelet artwork is concept imagery, not an official product photograph. The card and website both link to the official collection, and both identify this as an independent demo.

## License and credits

No license has been selected for this project's original code or media. Public GitHub visibility alone does not grant reuse rights. The bundled QR library and fonts retain their own notices in [`vendor/`](vendor/). Confirm media rights and [choose a project license](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) before inviting reuse or contributions.
