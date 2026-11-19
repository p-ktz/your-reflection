# Your Reflection

An independent, presentation-ready concept for a Perlée-inspired gift experience. The recipient scans a card in the jewelry box, enters a six-digit code, and explores three memories through glowing pearls on a bracelet.

## Demo flow

1. Open the [sample gift card](dist/gift-card.html), or print it and scan its QR code.
2. Enter the demo code **271846** on the landing page. The code is also visible on the card and as a presentation aid below the input.
3. Select any of the three glowing pearls. Two open the supplied photos; the third opens the supplied video.
4. Use Next/Previous, arrow keys, or a horizontal swipe to move between memories. Close with Escape.

For local preview, run `python3 -m http.server 8765 --directory dist` from this directory and open `http://127.0.0.1:8765/`.

## Files

- `dist/index.html`, `dist/styles.css`, `dist/app.js`: responsive experience and interactions.
- `dist/gift-card.html`, `dist/gift-card.css`: sample printable insert with QR and access code.
- `dist/assets/`: supplied memory media, a corrected web version of the video, product artwork created for this concept, QR, and caption file.
- `.openai/hosting.json`: static Sites deployment configuration.

## Design and frontend features

Editorial split-screen entry, responsive layout, subtle motion and texture, pointer-following light, glowing pearl hotspots, hover/focus tooltips, an accessible memory dialog, swipe and keyboard navigation, video captions, progress feedback, session-based demo unlock, reduced-motion support, and a printable QR card.

This is a **prototype**. The code is validated in the browser and is visible in the page source; it is not a secure authentication system. A production version would need a purchase-linked token, server-side authorization, private media storage, signed asset delivery, and a consent and retention flow for uploaded photos and video. The site is independently created and is not affiliated with Van Cleef & Arpels.
