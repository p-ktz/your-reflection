# Your Reflection

**A story in every pearl.** Your Reflection is a standalone, presentation-ready concept for a more personal jewelry gift experience. A recipient scans the card inside a gift box, enters a six-digit demo code, and explores memories hidden in three pearls on a bracelet.

> [!NOTE]
> This is an independent concept inspired by the [Van Cleef & Arpels Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html). It is not an official Van Cleef & Arpels website or product.

![Desktop view of Your Reflection showing the interactive gold bracelet and three memory pearls](docs/screenshots/bracelet.webp)

| Gift reveal | Access screen |
| --- | --- |
| ![Printable concept gift card with a QR code and six-digit demo code](docs/screenshots/gift-card.webp) | ![Your Reflection access screen asking for the code from the gift](docs/screenshots/access.webp) |

<img src="docs/screenshots/mobile.webp" alt="Mobile view of the bracelet experience with three glowing memory pearls" width="300">

The screenshots show an example host. Start the launcher before presenting so the gift card QR points to your own network address.

## The experience

1. A gift giver chooses memories to accompany a bracelet. This demo includes **two photos and one video** as sample memories.
2. The recipient finds a printed card with a QR code and six-digit code in the box.
3. Scanning the QR opens Your Reflection on the hosting laptop or server. The recipient enters **`271846`**.
4. Three glowing pearls on the bracelet reveal the memories. The recipient can continue through them, read a personal note, and follow a link to the [official Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html).

The gift giver's upload and purchase flow is a **concept only**; this repository implements the recipient experience and printable sample card.

### What is included

- Responsive desktop and mobile layouts, pearl hover/focus states, subtle motion, and a memory dialog.
- Keyboard navigation, touch swipe, visible focus, reduced-motion support, and captions for the video.
- A printable gift card whose QR is regenerated for the host's reachable address when the demo starts.
- A one-command Python launcher and a Docker Compose setup. Fonts, media, and the QR generator are bundled; the demo does not need an external API or database.

## Quick start with Docker

You need [Docker](https://docs.docker.com/get-docker/) with Compose. Download or clone this repository, open a terminal in its root directory, and set `PUBLIC_HOST` to the **LAN IPv4 address of the computer running Docker**. Replace the example address below with your own.

**Linux / macOS**

```bash
PUBLIC_HOST=192.168.1.23 docker compose up --build
```

**Windows PowerShell**

```powershell
$env:PUBLIC_HOST = "192.168.1.23"
docker compose up --build
```

Then open `http://192.168.1.23:8765/gift-card.html` (using *your* address), show or print the card, and scan its QR from a phone on the same Wi-Fi. The QR points to `http://192.168.1.23:8765/`. Enter **`271846`** to unlock the experience.

Keep Docker running during the presentation. Stop it with `Ctrl+C`, or run `docker compose down` from another terminal. Rebuild after editing the site with `docker compose up --build`.

> [!TIP]
> On a server, `PUBLIC_HOST` may be a DNS name that visitors can reach. Allow TCP port `8765` through the firewall. This setup serves HTTP and is intended for a controlled demo; add HTTPS and proper access control before any real customer deployment.

## Run without Docker

You need **Python 3.10+** and a modern browser. No `pip install` is required.

**Linux / macOS**

```bash
python3 launch_demo.py
```

You can also run `./start-demo.sh` on Linux/macOS.

**Windows PowerShell**

```powershell
py -3 launch_demo.py
```

The launcher detects a local address, refreshes the card's QR, prints both URLs, and opens the gift card in the host browser. Keep the terminal open until the presentation is finished; press `Ctrl+C` to stop.

If the wrong network adapter is selected, pass the address explicitly:

```bash
python3 launch_demo.py --host 192.168.1.23
```

Run `python3 launch_demo.py --help` for all options, including `--port`, `--bind`, `--no-browser`, and `--prepare-only`. On Windows, substitute `py -3` for `python3`.

## Presenting on a local network

1. Connect the hosting computer and visitors' phones to the **same Wi-Fi or LAN**. A guest network that isolates devices will not work.
2. Start the Python launcher or Docker Compose using the hosting computer's reachable IP address.
3. Open `/gift-card.html` on the host, then use **Print this sample card** if you want a physical insert.
4. Have a visitor scan the QR and enter **`271846`**. Select each of the three pearls to reveal the sample memories.

The hosting computer must remain on and connected. If its IP address changes, restart the demo and use the newly generated QR. The QR SVG included in a checkout is only a sample; starting the launcher updates it for the current host.

### Troubleshooting

| Problem | Check |
| --- | --- |
| The phone cannot open the QR link | Confirm both devices use the same network, the host is still running, and TCP port `8765` is allowed by the host firewall. Some guest Wi-Fi networks block device-to-device traffic. |
| The QR opens an old or wrong address | Restart the launcher after changing networks, or set `--host` (Python) / `PUBLIC_HOST` (Docker) to the host's reachable address. Reprint the card if necessary. |
| Port `8765` is already in use | Stop the other demo process. For Python, choose another port with `--port`; for Docker, adjust the published port and matching command in `compose.yaml`. |
| Docker says `PUBLIC_HOST` is missing | Set the variable in the **same terminal session** before running `docker compose up --build`. |

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

The six-digit code is a **visual demo step, not authentication**. The sample photos and video are served as ordinary static files to anyone who can reach the host. Use approved presentation media on a trusted network. A production version would need purchase-linked authorization, private media storage, consent, retention rules, and secure delivery.

**Before publishing this repository publicly**, review the rights and consent for every image and video in `dist/assets/` and for any screenshots in `docs/screenshots/`; replace them if needed. The bracelet artwork is concept imagery, not an official product photograph. The card and website both link to the official collection, and both identify this as an independent demo.

## License and credits

No license has been selected for this project's original code or media. Public GitHub visibility alone does not grant reuse rights. The bundled QR library and fonts retain their own notices in [`vendor/`](vendor/). Confirm media rights and [choose a project license](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) before inviting reuse or contributions.
