# browser-mcp-bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey)]()

A desktop tray application that bridges the [Browser MCP](https://browsermcp.io) stdio
server to **Streamable HTTP**, so HTTP-based MCP clients — like
[Open WebUI](https://openwebui.com/) or anything else on your network — can drive
**your actual, logged-in browser**.

```
┌──────────────┐   HTTP + Bearer    ┌──────────────────────────────┐
│ Open WebUI   │ ─────────────────► │ browser-mcp-bridge (tray)   │
│ (homelab)    │   :8020/mcp        │  ├─ stdio ─► @browsermcp/mcp│
└──────────────┘                    │  └────────► Browser ext.    │
                                    │              └─► your Chrome│
                                    └─────────────────────────────┘
```

## Why?

Browser MCP is a stdio MCP server that pairs with a Chrome extension and automates
*your real browser* — with your cookies, your sessions, your login state. Great idea,
but stdio means the MCP client has to run on the same machine. If your LLM frontend
lives on a homelab server (Open WebUI, etc.), it can't reach it.

**browser-mcp-bridge** closes that gap:

- 🌉 **stdio ⇄ HTTP** — exposes `@browsermcp/mcp` as a Streamable HTTP endpoint
- 🔐 **Bearer token auth** — every `/mcp` request must carry your token
- 🌐 **CIDR allowlist** — restrict which source IPs may connect (defaults to localhost only)
- 🖥️ **System tray app** — live status icon, settings GUI, log viewer
- 🩺 **Honest status light** — 3-state tray icon: green (browser connected),
  orange (bridge up, browser extension disconnected), red (subprocess down)
- 💓 **Heartbeat** — polls the browser with a read-only `browser_snapshot` every
  10s (configurable) so the status light reflects reality, not stale state
- 🛟 **Crash-resilient** — auto-restarts the npx subprocess with backoff; survives
  browser restarts
- 🩹 **Health endpoint** — `GET /health` (no auth) for monitoring from anywhere on the LAN

## Security model

This tool gives an LLM **full control of your real browser session**. Please read this.

| Layer | What it protects against |
|---|---|
| Bearer token | Anyone without the token (e.g. passing bots, LAN scanners) |
| CIDR allowlist | Anyone outside your allowed IP ranges (e.g. WAN exposure) |
| Plaintext HTTP | ⚠️ Nothing — token and traffic are unencrypted on the wire |

Recommended setup: **LAN-only deployment** (homelab), token in Open WebUI,
CIDR limited to your subnet. Do **not** expose this to the internet without
putting a TLS-terminating reverse proxy in front of it.

The token is stored in `~/.config/browser-mcp-bridge/config.json` (chmod 600).

## Requirements

- Python 3.10+
- Node.js (for `npx`, which fetches `@browsermcp/mcp`)
- Qt6/PySide6 (tray + GUI; headless mode works without it)
- [Browser MCP Chrome extension](https://chromewebstore.google.com/detail/browser-mcp/ndjkojkjnhpbfoihkeeahhefknkjhmgj)

## Install

```bash
git clone https://github.com/NopeNix/browser-mcp-bridge.git
cd browser-mcp-bridge
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Usage

### GUI (tray) mode

```bash
venv/bin/python bridge.py
```

Tray icon appears in your system tray (green → orange → red depending on state).
Right-click for: Show window · Restart subprocess · Quit.
The settings dialog lets you set **port**, **bearer token** (show/hide),
**CIDR allowlist**, and **heartbeat interval**.

### Headless mode

```bash
venv/bin/python bridge.py --headless
```

### Desktop integration (KDE/Plasma)

```bash
mkdir -p ~/.local/share/applications ~/.config/autostart
cp packaging/browser-mcp-bridge.desktop ~/.local/share/applications/
cp packaging/browser-mcp-bridge.desktop ~/.config/autostart/
```

### systemd user service (optional, headless servers)

```bash
cp packaging/browser-mcp-bridge.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now browser-mcp-bridge
```

> ⚠️ Run **either** the GUI or the headless service — they both bind the same
> port and spawn their own subprocess, so running both will conflict.

## Connecting Open WebUI

1. Admin Panel → Settings → Tools → add MCP server:
   `http://<bridge-host>:8020/mcp`
2. Auth: header `Authorization` = `Bearer <your-token>` (find it in the tray
   settings dialog)
3. In Chrome, click the Browser MCP extension icon → **Connect**
4. Tools (`browser_navigate`, `browser_click`, …) appear in the model's toolset

## Configuration

`~/.config/browser-mcp-bridge/config.json`:

```json
{
  "port": 8020,
  "token": "auto-generated-on-first-run",
  "allowed_cidrs": ["127.0.0.1/32", "::1/128"],
  "heartbeat_interval": 10
}
```

- `allowed_cidrs` — list of IPv4/IPv6 CIDRs permitted to call `/mcp`
- `heartbeat_interval` — seconds between read-only browser probes (status light refresh)

## Endpoints

| Route | Auth | Purpose |
|---|---|---|
| `GET /health` | none | `{"status":"ok","subprocess":true,"browser":"online"}` |
| `POST /mcp` | Bearer + CIDR | MCP Streamable HTTP endpoint |
| `DELETE /mcp` | Bearer + CIDR | session termination |

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Tray green, tools fail with "No connection to browser extension" | Extension not connected — click its icon → Connect |
| Tray orange | Bridge up, browser extension disconnected (checked every heartbeat) |
| Tray red | npx subprocess crashed — restart from tray menu |
| `/mcp` returns 403 | Your IP is not in `allowed_cidrs` |
| `/mcp` returns 401 | Missing or wrong bearer token |
| Port taken at startup | Another instance or service on that port — change `port` in config |

## Architecture

```
bridge.py          single-file app: HTTP server, subprocess manager, tray GUI
packaging/         .desktop launcher, systemd unit
```

The HTTP server is stdlib `http.server` (no aiohttp/flask dep for the server path);
PySide6 is only needed for the tray/GUI. Each HTTP request is translated 1:1 into a
JSON-RPC message over the subprocess's stdio, and responses are matched back by
request id.

## License

MIT — see [LICENSE](LICENSE).
