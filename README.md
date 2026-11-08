# 📱→🖥️ HDD Sync

A simple app that backs up photos, videos, and files from an **iPhone** to an
**external 1TB HDD** connected to an **Ubuntu laptop** — over local WiFi.

No cloud. No accounts. Files stay at home.

```
iPhone ──(WiFi)──> Ubuntu laptop ──(USB)──> 1TB HDD
  (web app)         (FastAPI server)        (organized folders)
```

---

## What it does

- ✅ Install like a real app on the iPhone home screen (it's a PWA — no App Store)
- ✅ Auto-sorts every file into folders: `images/`, `videos/`, `audio/`, `documents/`, `archives/`, `others/`
- ✅ **Skips duplicates** — syncing the same photo twice does nothing (same name + size = skip)
- ✅ Same name but different file? Saved as `photo (1).heic` — nothing is overwritten
- ✅ Shows upload progress bar and a friendly summary when done

---

## Project files

```
hddsync/
├── server.py      ← FastAPI server (sorts files, finds the HDD automatically)
├── index.html     ← the app UI shown on the iPhone
├── start.sh       ← one command to start everything
└── venv/          ← Python environment (created during setup)
```

---

## Setup (one time)

### 1. On Ubuntu — install & prepare

```bash
mkdir ~/hddsync && cd ~/hddsync
python3 -m venv venv && source venv/bin/activate
pip install fastapi "uvicorn[standard]" python-multipart
```

Put `server.py`, `index.html`, and `start.sh` in this folder.

Make the start script executable:

```bash
chmod +x start.sh
```

### 2. The HDD

Plug in the external HDD. The server **finds it automatically** — no need to
edit any path. It uses the first mounted drive under `/media/<your-username>/`.

### 3. Start the server

```bash
./start.sh
```

You should see a line like:

```
Uploads will go to: /media/yourname/DriveName/iphone_uploads
```

Find your laptop's IP (needed on the phone once):

```bash
hostname -I     # e.g. 192.168.0.105
```

---

## On the iPhone (one time)

1. Connect to the **same WiFi** as the laptop
2. Open **Safari** → go to `http://192.168.0.105:8008` (your laptop's IP)
3. Tap **Share** → **Add to Home Screen**
4. Done — it now opens like a normal app with its own icon

---

## Daily use

| Step | Action |
|------|--------|
| 1 | Plug the HDD into the laptop |
| 2 | Run `./start.sh` on the laptop |
| 3 | Open **HDD Sync** on the iPhone |
| 4 | Tap **Choose Files / Photos** → pick what to back up |
| 5 | Tap **⇪ Sync to HDD** |
| 6 | Wait for "✅ Synced: …" |

### Before unplugging the HDD ⚠️

Eject it safely first, or the last files may not be fully written:
click the **⏏** next to the drive in Ubuntu's Files app — or run `sync` in a
terminal and wait a few seconds.

---

## Where files land on the HDD

```
iphone_uploads/
├── images/      photos, screenshots (.heic .jpg .png …)
├── videos/      .mov .mp4 …
├── audio/       .m4a .mp3 …
├── documents/   .pdf .docx .txt …
├── archives/    .zip .rar …
└── others/      anything else
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "❌ Can't reach laptop" on phone | Same WiFi? Server running? IP changed? Run `hostname -I` again |
| "HDD not mounted" | Replug the USB cable, **restart the server** (it detects the drive at startup) |
| "Permission denied" error | Drive is probably NTFS mounted read-only → `sudo ntfsfix /dev/sdX1` (find name with `lsblk`), then replug |
| App stopped working after a while | Laptop IP changed — reserve a fixed IP for the laptop in your **router's DHCP settings** |
| 404 favicon in server log | Harmless, already handled — ignore |

---

## Tips

- **Fixed IP:** reserve the laptop's IP in router settings (DHCP reservation) so
  the iPhone bookmark never breaks.
- **Access from outside home WiFi:** install [Tailscale](https://tailscale.com)
  on both devices — then the app works anywhere, no router changes.
- **Auto-start the server on login:** ask me to set up a systemd user service.

---

## Tech notes

- Server: **Python / FastAPI**, port `8008`, plain HTTP (local network only)
- Client: single-file HTML/JS app, installable as a PWA via Safari
- Duplicate check: filename + file size (fast; good enough for photo backups)
- Why not a native iOS app? Building native iOS apps requires a Mac + Xcode.
  The PWA does the same job with zero cost. The FastAPI server would work
  unchanged as a backend for a native app later.
