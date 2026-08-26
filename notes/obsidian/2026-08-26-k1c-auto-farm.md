---
date: 2026-08-26
tags: [k1c, auto-farm, 3d-printing, moonraker]
---

# K1C Auto-Farm implementation dump

## Done in repo

Shipped `k1c-auto-farm/` as a self-contained mini-project (not mixed into ACL snippets):

- `ai_detector.py` — FastAPI detector with env config (`K1C_*`), fixed Moonraker multipart upload (`files` + `data={"print":"true"}`), optional Bearer token on mutating routes, `/healthz`, ready-state tolerance (`standby`/`complete`/`ready`) after clear streak
- `requirements.txt` + `.env.example`
- `macros/FORCE_EJECT.cfg` — example `FORCE_EJECT` + `PRINT_END_AUTO`
- `launchd/com.k1c.autofarm.detector.plist` — Mac Mini keep-alive template
- `README.md` — setup + curl cookbook
- `SMOKE_CHECKLIST.md` — supervised 2-job first success
- `tests/test_vision.py` — offline bed-clear unit tests

## Operator still owns

1. Set real `K1C_IP` / camera / Moonraker on LAN
2. Tune eject macros on the actual K1C
3. Capture empty-bed reference under overnight lighting
4. Run smoke checklist before unattended overnight

## Notes / gotchas

- Vision is absdiff %, not a trained model — lighting drift means re-capture reference
- Detector assumes eject already happened on print-end; it only starts the next queue job
- Keep `:8745` on trusted LAN or set `K1C_API_TOKEN`
