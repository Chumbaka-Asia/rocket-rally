<div align="center">

<img src="./images/screenshot.png" alt="Rocket Rally display with a fleet of coloured rockets" height="400" />

# Rocket Rally

[![Playground Commons](https://img.shields.io/badge/collection-Playground%20Commons-blue)](https://github.com/orgs/Chumbaka-Asia/repositories?q=topic%3Aplayground-commons)

A shared aerospace colouring installation: children colour a spacecraft, photograph it at a kiosk, and watch it join a racing fleet on the big screen.

[Overview](#overview) • [Features](#features) • [Getting Started](#getting-started) • [Exhibition Mode](#exhibition-mode) • [Display Settings](#display-settings) • [Export, Import & Gallery](#export-import--gallery) • [How It Works](#how-it-works) • [Project Structure](#project-structure)

</div>

## Overview

Rocket Rally lets children colour one of ten printable spacecraft templates, photograph it at a kiosk, and watch it burst out of a shared, wandering star gate to join a racing fleet — jostling, overtaking and banking through turns together.

The application has three pages:

| Page | Purpose |
| --- | --- |
| [`upload.html`](upload.html) | Kiosk page: pick a spacecraft, photograph the colouring, align the photo with the template outline, optionally name the child and the rocket, and launch it |
| [`display.html`](display.html) | The big-screen fleet. Rockets race through a retro cosmic scene, and the ⚙ **Mission control** panel holds the operator settings |
| [`gallery.html`](gallery.html) | Standalone viewer for exported fleet JSON files |

There are two ways to run it:

- **Single computer** — Open the HTML files directly in a browser. Rockets are saved in the browser (IndexedDB, with a `localStorage` fallback), and the upload and display tabs stay in sync through the BroadcastChannel API.
- **Exhibition** — Run the hub server (`scripts/server.py`). Any number of phones or tablets on the same Wi-Fi can launch rockets onto one shared display screen.

**Zero dependencies:** no build step, no `package.json`, no `npm install`. The app is plain HTML, CSS and JavaScript, and the artwork is generated in Canvas, CSS and SVG. The exhibition server uses the Python 3.7+ standard library only. Both pages work fully offline: the fonts (Unbounded and JetBrains Mono) are self-hosted under `fonts/` rather than loaded from Google Fonts, because a venue's Wi-Fi can be flaky or absent, and a display that silently falls back to system fonts mid-show is worse than one that never needed the network.

## Features

### Rockets

- **Ten printable spacecraft** — Classic Rocket, Winged Shuttle, Heavy-Lift Booster, Star Explorer, Saucer Scout, Star Whale, Comet Cat, Jelly Drifter, Dart Cruiser and Moon Hopper. Conventional rockets sit beside playful shapes, so a five-year-old and a ten-year-old both find one they like.
- **Own exhaust colour** — Each template has its own flame colour on the display, so a child can pick their rocket out of the pack by its flame as well as its shape.
- **Background removal** — The rocket is cut out of the photo using the template outline as a mask.
- **Alignment editor** — Drag, zoom and turn the photo to match the template outline before the rocket is cut out.
- **Optional names** — A child name (up to 20 characters) and a rocket name (up to 24 characters). If either is left blank, the launch and spotlight stay visual only; if both are filled in, a name banner appears.
- **Print template** — `colouring-templates/rocket-rally-template.pdf` is a printable template sheet, and each spacecraft is also an A4 SVG in `templates/`. Print at 100% scale. Printing all ten is a lot for a print station, so pick a subset if that suits the event.

### Display

- **The rally** — Rockets visibly race. Each keeps its own pace and occasionally surges past a neighbour, and the whole pack periodically banks and drifts. See [Rally motion](#rally-motion).
- **Arrivals** — The display queues up to three arrivals at once, speeds the shared starfield into a warp flash, and the new rocket bursts out of the gate, holds oversized for a moment, then banks into the front of the fleet.
- **Heading** — An editable title and subtitle (defaults "Rocket Rally" and "Shared starfleet"), the Chumbaka logo, a rocket count and a connection status readout.
- **Join code** — A QR code in a corner of the display that visitors can scan to open the upload page, or any other URL you choose.
- **Sound** — Background music (two tracks) and a launch sound. Muted by default. A credit line for the current track shows on the display.
- **Settings panel** — Controls for sound, join code, heading text, rally tempo, fleet size and scale, and archive export and import. See [Display Settings](#display-settings).
- **Demo mode** — A self-running showcase with sample rockets. See [Demo mode](#demo-mode).

### Sync & Persistence

- **Single computer** — Rockets are stored in the browser's IndexedDB (falling back to `localStorage`) and sent between tabs with BroadcastChannel.
- **Exhibition** — Rockets are stored in `rockets-data.json` on the hub computer and sent to display screens with Server-Sent Events (SSE). Every uploaded rocket stays there until an operator removes it or clears the fleet.
- **Export, import & gallery** — Export the whole fleet as a JSON file, restore it later, or browse it in `gallery.html`. See [Export, Import & Gallery](#export-import--gallery).

Every piece in this collection honours `prefers-reduced-motion`: motion is calmed, never blocked.

## Getting Started

> **Download:** Grab the ready-to-run app ZIP and printable spacecraft template PDF from the [**Latest Release**](../../releases/latest) page.

No installation or build step is needed. Open the files directly in any modern browser. For a multi-device setup, see [Exhibition Mode](#exhibition-mode).

### Quick start (single computer)

1. Open `display.html` in a browser tab.
2. Open `upload.html` in another tab of the same browser.
3. On the upload page: pick a spacecraft, choose a photo of the colouring, line it up under the outline and click **Cut it out**. Add names if you like, then click **Launch into space ✦**.
4. Switch to the display tab. The rocket bursts out of the star gate.

> [!NOTE]
> The upload and display pages must be opened in the same browser to share rockets in this mode. To share rockets between devices, use [Exhibition Mode](#exhibition-mode).

### Quick start (exhibition)

Use this when children launch rockets from phones or tablets onto one big screen.

1. Print some of the spacecraft sheets from `templates/` at 100% scale and hand out colouring materials.
2. Connect the hub computer and all other devices to the same Wi-Fi. A travel router works best.
3. On the hub computer, double-click `start.bat`. A window opens and shows the addresses.
4. On the display screen, open the "Display screen" address in a browser. Press **F11** for full screen.
5. On each phone or tablet, open the "Phone kiosks" address, or scan the join code on the display screen (turn it on in ⚙ **Mission control**).
6. Children photograph their colouring, align it under the outline, optionally name themselves and their rocket, and launch it. It appears on the display within a few seconds.

When you are done, press **Ctrl+C** in the `start.bat` window to stop the hub. To start fresh next time, click ⚙ → **Clear fleet** on the display screen.

For more detail, see [Exhibition Mode](#exhibition-mode).

### Demo mode

Add `?demo` to the display address to see the display with sample rockets and no real data. For example `display.html?demo`, or `http://<host>:8082/display.html?demo` while the server is running.

- 12 colourful test rockets fly on load (the first ten use the sample images `test-rocket-01.png` to `test-rocket-10.png` in `images/`), and a random one re-launches every 5 seconds to exercise arrivals continuously. Use `?demo=100` to choose the number of rockets (1–300).
- The connection readout shows **Test flight**. Demo mode never connects to the hub or reads the stored fleet.

## Exhibition Mode

Run a local hub server so multiple kiosks (phones, tablets, laptops) can launch rockets onto a single shared display screen over Wi-Fi. No internet connection is needed.

### Requirements

- Python 3.7+ on the hub computer (standard library only, no `pip install`)
- All devices on the same Wi-Fi network

### Setup

**On the hub computer** (the one connected to the display screen):

1. Double-click `start.bat`, or run `python scripts/server.py` from the project folder. To use a different port, add it at the end: `python scripts/server.py 9001`. The default port is 8082.
2. The server prints the addresses to use:

   ```text
   Rocket Rally is ready
     Display screen -> http://localhost:8082/display.html
     Phone kiosks   -> http://192.168.1.5:8082/upload.html
     Templates      -> cat, classic, dart, explorer, heavy, hopper, jelly, saucer, shuttle, whale
     Press Ctrl+C to stop.
   ```

3. Open the display address in a browser on the display screen.

**On each kiosk** (any device on the same Wi-Fi):

1. Open the "Phone kiosks" address in a browser, or scan the join code shown on the display screen.
2. Launch a rocket. It appears on the display screen within a few seconds.

> [!TIP]
> Write the upload address on a card at each station so visitors can type it in easily.

### Network options

| Option | Setup | Notes |
| --- | --- | --- |
| Venue Wi-Fi | Connect all devices to the existing Wi-Fi | No setup, but depends on the venue's network |
| Travel router | Plug in a router and connect all devices to it | Self-contained, no internet needed. **Recommended** |
| Windows Mobile Hotspot | Turn on in Settings → Network → Mobile Hotspot | No extra hardware. One-time setup on the hub computer |

> [!NOTE]
> A travel router creates a private Wi-Fi network that does not depend on the venue's internet.

### Connection status

When the display is served by the hub, the readout in the top corner shows the connection status: **Mission control connected** when the live link is up, **Reconnecting to hub…** when it drops, and **Hub offline** if the saved fleet could not be loaded. When the files are opened directly, it reads **Local flight mode**.

### Between sessions

- To remove all rockets, open the display screen, click ⚙, then **Clear fleet** and tap again to confirm. This clears every connected screen and empties `rockets-data.json`.
- If the hub computer restarts, saved rockets load again from `rockets-data.json`. On reload or server restart they return quietly, without replaying every launch.
- The display shows the newest rockets up to the **Max rockets** limit. Older rockets stay saved and reappear if that limit rises.

### Server API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/rockets` | Return the current fleet as a JSON array |
| `POST` | `/api/rockets` | Submit a rocket, save it and send it to all display screens |
| `POST` | `/api/rockets/import` | Quietly restore an archive (`{"rockets": [...]}`, 1–500 rockets) |
| `DELETE` | `/api/rockets/<id>` | Remove one rocket |
| `DELETE` | `/api/rockets` | Clear the fleet |
| `GET` | `/api/events` | SSE stream (`new-rocket`, `sync-rockets`, `remove-rocket` and `clear` events) |
| `GET` | `/api/host-info` | Return the server's local network IP and port (`{ip, port}`). The display uses this to build the join code address. |
| `GET` | any other path | Serve files from the project folder |

The server sends a keep-alive ping every 25 seconds on each SSE connection and allows cross-origin requests (CORS) on the API. It writes `rockets-data.json` atomically, so shutting down or restarting the hub does not discard the fleet. The template allowlist for uploads is derived at startup from `templates/*.svg` and printed to the console.

Submissions are checked before they are saved: the image must be a WebP or PNG data URL (up to about 1.8 MB), the child name at most 20 characters, the rocket name at most 24 characters, and the template one of the ids found in `templates/`.

## Display Settings

Click ⚙ in the corner of `display.html` to open **Mission control**. All settings except the sound switch are remembered by the browser. Sound is muted every time the page loads.

| Section | Control | What it does |
| --- | --- | --- |
| **Sound** | Enable / Mute | Turns the background music and the launch sound on or off. Muted by default. |
| | Repeat current song | Keeps replaying the current track instead of moving on to the next. |
| **Join code** | Show / Hide | Shows or hides the QR code on the display. Hidden by default. |
| | URL | Upload page (auto) or Custom URL (see below). |
| **Display text** | Title, Subtitle | Heading text on the display (up to 30 and 60 characters). Leave blank for "Rocket Rally" and "Shared starfleet". |
| **Rally tempo** | Orbit speed (0–100) | How fast the pack orbits. Default is 50. |
| | Scramble (0–100) | How much the pack jostles and overtakes. Default is 50. |
| | Reset defaults | Sets both sliders back to 50. |
| **Fleet display** | Max rockets (50–500) | Maximum number of rockets shown. Default is 200. The newest rockets are shown and all rockets stay in the archive. |
| | Rocket scale (50%–150%) | Overall rocket size. Default is 100%. |
| **Fleet archive** | Export / Import | Download or restore a JSON backup. See [Export, Import & Gallery](#export-import--gallery). |
| **Recent rockets** | × | Remove a single recent rocket. |
| **Clear fleet** | Clear fleet | Removes every rocket. See below. |

The right feel for **Rally tempo** depends on the physical screen and the room, so it is tunable without touching code.

> [!WARNING]
> **Clear fleet** removes every stored rocket from the hub and from every connected display, and it cannot be undone. The button asks for a second tap to confirm instead of showing a browser dialog. Export the fleet first if you want to keep it.

### QR code

The QR code is generated in the browser. **URL** has two options:

- **Upload page (auto)** — Links to `upload.html` on the hub computer's network address. Only works when the display is served by the hub server, so it is unavailable when the files are opened directly.
- **Custom URL** — Links to any address you type. Works in every mode. If the box is empty, or the address is too long for a QR code, no QR code is shown.

### Clearing rockets

- **Single computer:** Clear fleet removes the rockets stored in this browser.
- **Exhibition:** Clear fleet removes all rockets from the hub and from every connected screen.

## Export, Import & Gallery

### Export

Open ⚙ **Mission control** and click **Export** under **Fleet archive** to download a JSON file (`rocket-rally-YYYY-MM-DD.json`) with every rocket, including its image (as a data URL) and names.

You can also remove a single rocket from the **Recent rockets** list with its **×** button.

### Import

Click **Import** in the same panel and choose a previously exported JSON file. Entries without an image or with an unknown template are skipped, and the rest are restored quietly: they join the display without replaying their launch. They are saved in the browser (single computer) or on the hub server (exhibition), where they receive new ids. The panel tells you how many rockets were restored, or that the file was not a valid Rocket Rally export.

The hub accepts imports of 1–500 rockets at a time.

### Gallery page

Open [`gallery.html`](gallery.html) in a browser, including directly from your files. Choose or drop an exported JSON file (or the hub's `rockets-data.json`) to see each rocket with its name, crew name, spacecraft, ID and launch date.

- Search by rocket name, child name, spacecraft or ID
- Filter by spacecraft, and sort by export order, newest first or oldest first
- Click **Download HTML gallery** to save a self-contained copy that opens with all rockets already loaded. Keep the original JSON file if you want to import the rockets back into the display.

The gallery reads the file in your browser only. It does not change the file or the live display. Records without a valid ID or image are skipped, and the page tells you how many were skipped. The page uses the self-hosted fonts in `fonts/`, so a downloaded copy moved elsewhere falls back to system fonts.

## How It Works

### Image processing

On `upload.html`:

1. **Pick your spacecraft** — Choose one of the ten templates.
2. **Photograph your colouring** — Take a photo of the whole page (bright, even light helps) or choose an image file.
3. **Line it up** — Drag the photo, and use the **Zoom** and **Turn** sliders, until it matches the template outline.
4. **Cut it out** — The template outline (`mask` in `ROCKET_TEMPLATES`) is applied to the aligned photo, and everything outside the rocket becomes transparent.
5. **Name it or launch it** — Check the preview, optionally enter the child and rocket names, and click **Launch into space ✦**.

The final transparent image is encoded as WebP (quality 0.86), or PNG if the browser cannot produce WebP. No camera stream is sent anywhere. Only the final rocket image and any entered names are submitted to the local server, and they stay on the hub until cleared.

### Rally motion

Rockets don't just orbit — the fleet visibly races:

- Each rocket keeps its own pace and occasionally surges past a neighbour.
- The whole pack periodically banks and drifts.
- The shared vanishing point (the "gate") wanders across the screen on its own schedule rather than sitting fixed at centre, so the scene reads as a curving track rather than a stationary hub.
- Depth, and therefore size and draw order, is strictly tied to age: the newest rocket is always the largest and always draws in front. An older rocket occasionally gets pulled forward for a spotlight lap, but is capped just short of the newest arrival's prominence.

None of this is scored or ranked. It's energy, not competition.

### Sync mechanism

The pages check `window.location.protocol` to choose a mode:

| Mode | Address starts with | Live updates | Rocket storage |
| --- | --- | --- | --- |
| **Single computer** | `file:` | `BroadcastChannel('rocket-rally')` | IndexedDB (`RocketStore` in `scripts/rocket-core.js`), `localStorage` fallback |
| **Exhibition** | `http:` or `https:` | SSE from `/api/events` | `rockets-data.json` on the hub |

The heading text, join code, tempo and fleet display settings are saved in the browser's `localStorage` in both modes.

### Data flow

**Single computer** (files opened directly):

```text
[Upload page] -- BroadcastChannel --> [Display page]
      |                                    |
      +------------ IndexedDB <------------+
```

**Exhibition** (served by `scripts/server.py`):

```text
[Kiosk 1] -+
[Kiosk 2] -+-- POST /api/rockets --> [server.py] -- SSE /api/events --> [Display screen]
[Kiosk 3] -+                              |
                                   rockets-data.json
```

### Rocket object structure

Each rocket on the server or in an export file has these fields:

| Field | Type | Description |
| --- | --- | --- |
| `version` | number | Record format version (currently `1`) |
| `id` | string | Unique ID (assigned by the server in exhibition mode) |
| `imageDataURL` | string | WebP or PNG data URL of the cut-out rocket |
| `templateId` | string | Template id, matching a file in `templates/` (for example `classic`) |
| `childName` | string | Optional child name (max 20 characters, may be empty) |
| `rocketName` | string | Optional rocket name (max 24 characters, may be empty) |
| `createdAt` | number | Time created, in milliseconds since 1970 |

### Adding a template

Adding an eleventh template needs only a new `templates/<id>.svg` (matching the existing A4 convention) and a matching entry in `ROCKET_TEMPLATES` in `scripts/rocket-core.js` — its `label`, `file`, outline `mask`, `engines` positions and `flame` colours. The server's upload allowlist is derived automatically from whatever SVGs are in `templates/`, so nothing in `scripts/server.py` needs to change.

## Project Structure

```text
├── upload.html              Kiosk page: pick, photograph, align, name and launch
├── display.html             Big-screen fleet display and Mission control
├── gallery.html             Viewer for exported fleet JSON files
├── start.bat                Double-click launcher for scripts/server.py
├── scripts/
│   ├── server.py            Hub server for exhibition mode
│   ├── rocket-core.js       Shared templates, helpers and IndexedDB rocket store
│   └── qr.js                QR code library (qrcode-generator, MIT)
├── templates/
│   ├── classic.svg          Printable A4 spacecraft (one <id>.svg per template)
│   ├── shuttle.svg
│   ├── heavy.svg
│   ├── explorer.svg
│   ├── saucer.svg
│   ├── whale.svg
│   ├── cat.svg
│   ├── jelly.svg
│   ├── dart.svg
│   └── hopper.svg
├── colouring-templates/
│   └── rocket-rally-template.pdf   Printable template sheet
├── images/
│   ├── chumbaka-logo.png    Logo shown in the display heading
│   ├── screenshot.png       Screenshot used in this README
│   └── test-rocket-01.png   Sample rocket images for demo mode (01 to 10)
├── fonts/                   Self-hosted Unbounded and JetBrains Mono (.woff2)
├── sounds/                  Background music tracks, with credits in README.md
├── effects/                 Launch sound effect, with credit in README.md
└── rockets-data.json        Hub server storage (created automatically)
```

## Acknowledgements

- Music and sound effects are from [Pixabay](https://pixabay.com/): background music by Maksym Malko and Dmitrii Kolesnikov, and the launch sound by Game Studio. Full links are in `sounds/README.md` and `effects/README.md`.
- `scripts/qr.js` is Kazuhiko Arase's [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) (MIT-licensed, licence header retained), vendored so the join code works fully offline.
- Fonts are [Unbounded](https://fonts.google.com/specimen/Unbounded) and [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono), both self-hosted.
