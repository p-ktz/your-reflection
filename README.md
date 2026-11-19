# Your Reflection

**A story in every pearl.** An independent, presentation-ready concept inspired by the [Van Cleef & Arpels Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html). The recipient scans the card inside the jewelry box, enters a six-digit code, and discovers two photos and one video by selecting three glowing pearls on a bracelet.

The experience is in English. The card and the experience both link to the official collection. This project is not affiliated with Van Cleef & Arpels.

## Quick start: laptop or another computer

Requirements: **Python 3.10+**, a modern browser, and a local network. No `pip install` is needed; the QR generator and fonts are included.

1. Copy this entire `your-reflection` folder to the computer that will host the demo.
2. Connect that computer and visitors' phones to the **same Wi-Fi or LAN**.
3. In a terminal inside this folder, run:

   ```bash
   python3 launch_demo.py
   ```

   On Windows, use `py -3 launch_demo.py`. On Linux/macOS, `./start-demo.sh` is another option.
4. The gift card opens in the host computer's browser. The terminal also prints its URL and the guest URL. Show or print the card; its QR is regenerated for that computer's current network address each time the launcher starts.
5. Scan the QR on a phone and enter the sample code **271846**. Select the three glowing pearls to open the memories.
6. Keep the terminal open during the presentation. Press `Ctrl+C` to stop the server.

If automatic IP detection chooses the wrong adapter, pass the computer's LAN IP explicitly, for example `python3 launch_demo.py --host 192.168.1.23`. If the network isolates connected devices or a firewall blocks TCP port **8765**, phones cannot reach the host. When the computer changes networks, restart the launcher and show or print the new QR.

## Run with Docker

Requirements: Docker Engine or Docker Desktop with **Docker Compose v2**. Set `PUBLIC_HOST` to an IP or DNS name that visitors can reach. This value is placed in the QR; the container's own address must not be used.

Linux/macOS:

```bash
PUBLIC_HOST=192.168.1.23 docker compose up --build
```

Windows PowerShell:

```powershell
$env:PUBLIC_HOST="192.168.1.23"
docker compose up --build
```

Open `http://192.168.1.23:8765/gift-card.html` on the host or another device, using the same address you set above. The QR opens `http://192.168.1.23:8765/`. For a demo server with DNS, set `PUBLIC_HOST` to the domain and allow TCP port 8765 through the server firewall. Stop with `Ctrl+C` or `docker compose down`. Rebuild with `docker compose up --build` after editing the site.

Docker publishes port **8765**. The built image contains the site, media, fonts, launcher, and QR generator. No mounted volumes, database, API keys, or external services are required.

## What to show in the presentation

1. Start at the printable [gift card](dist/gift-card.html) and explain how the package reveals the QR and code.
2. Scan or open the QR destination, enter **271846**, and point to the three glowing pearls.
3. Open both photos and the video. Try hover, Next/Previous, arrow keys, touch swipe, and the video's captions.
4. Finish at the link to the [official Perlée collection](https://www.vancleefarpels.com/ae/en/collections/jewelry/perlee.html).

The layout supports desktop and mobile screens, keyboard focus, reduced motion, and a printable card. The visual effects include pearl highlights, subtle motion, pointer-responsive light, and an editorial layout.

## Project files

| Path | Purpose |
| --- | --- |
| `dist/index.html`, `dist/styles.css`, `dist/app.js` | Main experience and interactions |
| `dist/gift-card.html`, `dist/gift-card.css` | Printable sample card |
| `dist/fonts.css`, `dist/assets/fonts/` | Locally hosted fonts for offline presentation |
| `dist/assets/` | Bracelet artwork, two photos, video, poster, captions, and generated QR |
| `launch_demo.py`, `start-demo.sh` | Local server and QR refresh |
| `Dockerfile`, `compose.yaml`, `.dockerignore` | Container build and run configuration |
| `vendor/` | QR generator and third-party font licenses |

## Git and demo privacy

The project is a local Git repository on the `main` branch. `git log --oneline` shows its change history, and `git status` shows future edits. There is **no GitHub remote or automatic publishing**. If you later publish this repository publicly, review or replace the personal photos and video under `dist/assets/` first.

The six-digit code is a **demo interaction**, not real access control: the files are served directly to anyone who can reach the host. Use this version with presentation media on a trusted network. A real customer product needs purchase-linked server authorization, private storage, consent, retention rules, and secure delivery.
