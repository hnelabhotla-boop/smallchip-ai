# Installing SmallChip AI Desktop App

## Quick start (macOS)

1. **Download** [`SmallChip-AI-v0.2.0-macOS.zip`](releases/SmallChip-AI-v0.2.0-macOS.zip) from the [latest release](https://github.com/hnelabhotla-boop/smallchip-ai/releases)
2. **Unzip** the downloaded file
3. **Remove the macOS quarantine flag** (the app is unsigned; macOS will block it otherwise):
   ```bash
   xattr -dr com.apple.quarantine "SmallChip AI.app"
   ```
4. **Drag** `SmallChip AI.app` to `/Applications`
5. **First launch**: right-click the app → **Open** → confirm
6. The app will auto-start the FastAPI backend and open a native window

> **Why the "damaged" error?** The app is unsigned because Apple Developer ID costs $99/year. For a high school ISEF project, the right-click → Open workaround is fine. To eliminate the warning for everyone, sign with a Developer ID and notarize with `notarytool`.

## Run from source (any OS)

Works on macOS, Linux, Windows.

```bash
git clone https://github.com/hnelabhotla-boop/smallchip-ai.git
cd smallchip-ai
pip install -r requirements.txt
pip install -r requirements-desktop.txt
python desktop_app.py
```

The window opens at `http://localhost:8000`. If port 8000 is taken, set `SMALLCHIP_PORT=8001` first.

## Build the .app yourself

```bash
pip install pyinstaller
pyinstaller --name "SmallChip AI" \
    --windowed \
    --icon web/icon-512.png \
    --add-data "web:web" \
    --noconfirm \
    desktop_app.py
# Output: dist/SmallChip AI.app
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "SmallChip AI is damaged and can't be opened" | Run `xattr -dr com.apple.quarantine "SmallChip AI.app"` |
| "SmallChip AI cannot be opened because the developer cannot be verified" | Right-click → Open → confirm |
| Port 8000 already in use | Set `SMALLCHIP_PORT=8001` before launching |
| Backend fails to start | Run `uvicorn chipmind.api.server:app --host 127.0.0.1 --port 8000` manually to see the error |
| Window is blank | Backend isn't running. The app will show a "couldn't connect" page. Start the backend or use `python desktop_app.py` which auto-starts it. |
