# Supervised 2-job smoke checklist

Do this once before leaving the farm unattended overnight.

## Before you start

- [ ] Moonraker opens: `http://<K1C_IP>:7125/printer/info`
- [ ] Camera snapshot opens: `http://<K1C_IP>:8080/?action=snapshot`
- [ ] `FORCE_EJECT` run once by hand from Fluidd/Mainsail — part clears the bed
- [ ] Slicer end gcode calls `PRINT_END_AUTO` (or equivalent that ends with eject)
- [ ] Detector running on Mac Mini (`python ai_detector.py` or launchd)
- [ ] `curl http://MINI:8745/healthz` shows moonraker + camera pass (reference may still fail)

## Capture reference

- [ ] Bed empty, lighting matches how you will run overnight
- [ ] `curl -X POST http://MINI:8745/capture-reference`
- [ ] `curl -X POST http://MINI:8745/detect` → `"clear": true` with low `diff_percent`
- [ ] Place a scrap part on the bed → `/detect` → `"clear": false`

## Queue two small jobs

- [ ] Slice two short gcodes (`smoke_a.gcode`, `smoke_b.gcode`)
- [ ] Upload both:

```bash
curl -X POST http://MINI:8745/upload -F "file=@smoke_a.gcode"
curl -X POST http://MINI:8745/upload -F "file=@smoke_b.gcode"
curl http://MINI:8745/status | jq '.queue'
```

- [ ] Queue lists both files in alphabetical start order (rename if you need a specific order)

## Run the handoff (watch the whole time)

- [ ] Enable loop: `curl -X POST http://MINI:8745/auto-loop/true`
- [ ] Printer idle → detector starts `smoke_a` (or start manually: `POST /start-job/smoke_a.gcode`)
- [ ] Print finishes → eject runs on printer
- [ ] Logs show three clear detections (`Bed clear detected (1/3)` … `(3/3)`)
- [ ] `smoke_b` uploads and starts **without** touching the Mini
- [ ] `smoke_a` appears under `~/k1c_queue/completed/`

## Pass / fail

**Pass:** job 2 starts after eject + clear streak with no manual API calls after enabling auto-loop.

**Fail — common fixes**

| Symptom | Fix |
|---------|-----|
| Never starts job 2 | Check printer state after eject (`/status`); tune macros so state reaches standby/complete/ready |
| False “occupied” forever | Re-capture reference; raise `K1C_THRESHOLD` slightly; fix lighting |
| False “clear” with part on bed | Lower `K1C_THRESHOLD`; improve camera angle |
| Upload/start fails | Confirm Moonraker file upload works from Fluidd; check detector logs |
| Eject leaves part on bed | Fix mechanical eject before relying on vision |

## After a pass

- [ ] Disable auto-loop when done testing: `POST /auto-loop/false`
- [ ] For overnight: queue real jobs, re-enable auto-loop, leave filament + eject path trusted
