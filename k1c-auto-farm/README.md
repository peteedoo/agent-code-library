# K1C Auto-Farm Detector

Unattended Creality K1C print loop: Mac Mini watches the printer webcam, waits until the bed matches an empty reference, then uploads the next `.gcode` via Moonraker.

## Layout

```
k1c-auto-farm/
  ai_detector.py
  requirements.txt
  .env.example
  macros/FORCE_EJECT.cfg      # example Klipper macros
  launchd/com.k1c.autofarm.detector.plist
  SMOKE_CHECKLIST.md          # first supervised 2-job run
```

## Prerequisites

- K1C on LAN with Moonraker (`:7125`) and a snapshot camera (`:8080/?action=snapshot`)
- Mac Mini (or any always-on host) on the **same LAN**
- Working physical eject + Klipper macros (`FORCE_EJECT`, end-gcode calling `PRINT_END_AUTO`) — see `macros/`
- Python 3.10+

## One-time setup (Mac Mini)

```bash
cd k1c-auto-farm
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env → set K1C_IP to your printer
python ai_detector.py
```

Service listens on `http://0.0.0.0:8745` by default.

### Keep-alive (launchd)

1. Edit paths + `K1C_IP` in [`launchd/com.k1c.autofarm.detector.plist`](launchd/com.k1c.autofarm.detector.plist)
2. `cp launchd/com.k1c.autofarm.detector.plist ~/Library/LaunchAgents/`
3. `mkdir -p ~/.k1c_auto_farm && launchctl load ~/Library/LaunchAgents/com.k1c.autofarm.detector.plist`

### Printer macros

Merge [`macros/FORCE_EJECT.cfg`](macros/FORCE_EJECT.cfg) into Klipper config, tune coordinates, save & restart. Call `PRINT_END_AUTO` (or `FORCE_EJECT`) from slicer end gcode. Test eject **by hand** once before enabling auto-loop.

## Curl cookbook

Replace `MINI` with the Mac Mini IP (or `localhost` if on the Mini).

```bash
# Health / status
curl -sS http://MINI:8745/healthz | jq
curl -sS http://MINI:8745/status | jq

# Capture empty-bed reference (bed must be empty, lighting = overnight lighting)
curl -sS -X POST http://MINI:8745/capture-reference | jq

# One-shot bed detect
curl -sS -X POST http://MINI:8745/detect | jq

# Queue a gcode
curl -sS -X POST http://MINI:8745/upload \
  -F "file=@/path/to/part_a.gcode" | jq

# List queue via status
curl -sS http://MINI:8745/status | jq '.queue, .printer_state, .auto_loop'

# Enable / disable auto-loop
curl -sS -X POST http://MINI:8745/auto-loop/true | jq
curl -sS -X POST http://MINI:8745/auto-loop/false | jq

# Manual controls
curl -sS -X POST http://MINI:8745/trigger-eject | jq
curl -sS -X POST http://MINI:8745/pause | jq
curl -sS -X POST http://MINI:8745/resume | jq
curl -sS -X POST http://MINI:8745/cancel | jq
curl -sS -X POST http://MINI:8745/emergency-stop | jq

# Start a specific queued file
curl -sS -X POST http://MINI:8745/start-job/part_a.gcode | jq

# Remove from queue
curl -sS -X DELETE http://MINI:8745/queue/part_a.gcode | jq

# Recent logs
curl -sS 'http://MINI:8745/logs?lines=50' | jq
```

You can also drop files straight into `~/k1c_queue/` on the Mini; completed jobs move to `~/k1c_queue/completed/`.

## Env vars

| Variable | Default | Meaning |
|----------|---------|---------|
| `K1C_IP` | `192.168.1.100` | Printer IP |
| `K1C_MOONRAKER_PORT` | `7125` | Moonraker |
| `K1C_CAMERA_PORT` | `8080` | Webcam snapshot/stream |
| `K1C_HOST` / `K1C_PORT` | `0.0.0.0` / `8745` | Detector bind |
| `K1C_THRESHOLD` | `12.0` | Max % pixel diff = “clear” |
| `K1C_CONFIRMATION_COUNT` | `3` | Consecutive clear reads |
| `K1C_POLL_INTERVAL` | `10` | Seconds between polls |
| `K1C_AUTO_START` | `false` | Enable auto-loop on boot |
| `K1C_API_TOKEN` | empty | When set, mutating routes need `Authorization: Bearer <token>` |

Example with token:

```bash
curl -sS -X POST http://MINI:8745/auto-loop/true \
  -H "Authorization: Bearer change-me" | jq
```

## How the loop works

Every `K1C_POLL_INTERVAL` seconds, if auto-loop is on:

1. If printer state is `complete` → snapshot vs reference
2. Clear streak increments; occupied resets it
3. After N clear frames → short wait → start next queued gcode when printer is `standby` / `complete` / `ready`
4. If printer is already `standby` with no tracked job and the queue is non-empty → start the first file

Vision: grayscale + blur + absdiff. Re-capture the reference if lighting changes.

## First success

Follow [`SMOKE_CHECKLIST.md`](SMOKE_CHECKLIST.md) — one supervised 2-job handoff before overnight runs.

## Safety

- Detector does **not** replace a working eject path; it only starts the next job after the bed looks empty.
- `:8745` has no auth by default — keep it on a trusted LAN.
- Keep emergency-stop reachable (API or printer UI).
