#!/usr/bin/env python3
"""
K1C Auto-Farm AI Detector
FastAPI service intended for a Mac Mini on the same LAN as the printer.
Detects if the bed is clear by comparing the live camera snapshot to a reference image.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Optional

from contextlib import asynccontextmanager

import cv2
import numpy as np
import requests
import uvicorn
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==================== CONFIG ====================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="K1C_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ip: str = Field(default="192.168.1.100", description="Printer LAN IP")
    moonraker_port: int = 7125
    camera_port: int = 8080
    host: str = "0.0.0.0"
    port: int = 8745

    threshold: float = 12.0
    confirmation_count: int = 3
    poll_interval: int = 10
    auto_start: bool = False
    api_token: str = ""

    home: Path = Field(default_factory=lambda: Path.home())

    @property
    def moonraker_url(self) -> str:
        return f"http://{self.ip}:{self.moonraker_port}"

    @property
    def camera_snapshot_url(self) -> str:
        return f"http://{self.ip}:{self.camera_port}/?action=snapshot"

    @property
    def camera_stream_url(self) -> str:
        return f"http://{self.ip}:{self.camera_port}/?action=stream"

    @property
    def ref_image_path(self) -> Path:
        return self.home / ".k1c_auto_farm" / "bed_empty_reference.jpg"

    @property
    def captures_dir(self) -> Path:
        return self.home / "k1c_captures"

    @property
    def queue_dir(self) -> Path:
        return self.home / "k1c_queue"

    @property
    def log_path(self) -> Path:
        return self.home / ".k1c_auto_farm" / "detector.log"


settings = Settings()

for d in [settings.ref_image_path.parent, settings.captures_dir, settings.queue_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ==================== STATE ====================
class FarmState:
    def __init__(self):
        self.reference_image: Optional[np.ndarray] = None
        self.auto_loop_enabled = settings.auto_start
        self.last_status = "standby"
        self.clear_streak = 0
        self.current_job: Optional[str] = None
        self.log_entries: list[str] = []
        self.load_reference()

    def load_reference(self):
        if settings.ref_image_path.exists():
            self.reference_image = cv2.imread(str(settings.ref_image_path))
            self.log("Reference image loaded")
        else:
            self.log("No reference image set — capture empty bed first")

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.log_entries.append(entry)
        self.log_entries = self.log_entries[-200:]
        with open(settings.log_path, "a") as f:
            f.write(entry + "\n")
        print(entry)


state = FarmState()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    asyncio.create_task(auto_loop())
    state.log("K1C Auto-Farm Detector started")
    yield


app = FastAPI(
    title="K1C Auto-Farm Detector",
    version="1.1.0",
    lifespan=lifespan,
)


# ==================== OPTIONAL TOKEN ====================
def require_token(authorization: Optional[str] = Header(default=None)):
    """When K1C_API_TOKEN is set, mutating routes require Authorization: Bearer <token>."""
    if not settings.api_token:
        return
    provided = authorization or ""
    if provided.startswith("Bearer "):
        provided = provided[7:].strip()
    else:
        provided = provided.strip()
    if provided != settings.api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


Mutating = Depends(require_token)


# ==================== MOONRAKER HELPERS ====================
def moonraker_get(endpoint: str, timeout: int = 10):
    try:
        r = requests.get(f"{settings.moonraker_url}{endpoint}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        state.log(f"Moonraker GET error: {e}")
        return None


def moonraker_post(
    endpoint: str,
    json_data=None,
    files=None,
    data=None,
    timeout: int = 30,
):
    """POST to Moonraker. Supports JSON body and/or multipart file upload."""
    try:
        r = requests.post(
            f"{settings.moonraker_url}{endpoint}",
            json=json_data,
            files=files,
            data=data,
            timeout=timeout,
        )
        r.raise_for_status()
        # Some Moonraker responses are empty
        if not r.content:
            return {"ok": True}
        return r.json()
    except Exception as e:
        state.log(f"Moonraker POST error: {e}")
        return None


def get_printer_status():
    data = moonraker_get("/printer/objects/query?print_stats")
    if data and "result" in data:
        return data["result"]["status"]["print_stats"]["state"]
    return "unknown"


def get_temps():
    data = moonraker_get("/printer/objects/query?heater_bed&extruder")
    if data and "result" in data:
        s = data["result"]["status"]
        return {
            "bed": round(s.get("heater_bed", {}).get("temperature", 0), 1),
            "bed_target": round(s.get("heater_bed", {}).get("target", 0), 1),
            "nozzle": round(s.get("extruder", {}).get("temperature", 0), 1),
            "nozzle_target": round(s.get("extruder", {}).get("target", 0), 1),
        }
    return {"bed": 0, "bed_target": 0, "nozzle": 0, "nozzle_target": 0}


def get_progress():
    data = moonraker_get("/printer/objects/query?display_status")
    if data and "result" in data:
        d = data["result"]["status"]["display_status"]
        return {
            "progress": round(d.get("progress", 0) * 100, 1),
            "message": d.get("message", ""),
        }
    return {"progress": 0, "message": ""}


def get_queue():
    data = moonraker_get("/server/job_queue/status")
    if data and "result" in data:
        return data["result"].get("queued_jobs", [])
    return []


def upload_and_start(gcode_path: Path):
    """Upload a gcode file to Moonraker and start printing immediately."""
    with open(gcode_path, "rb") as f:
        return moonraker_post(
            "/server/files/upload",
            files={"file": (gcode_path.name, f, "application/octet-stream")},
            data={"print": "true"},
        )


def start_next_queued_job():
    queue = sorted(settings.queue_dir.glob("*.gcode"))
    if not queue:
        state.log("Queue empty — nothing to start")
        return False

    next_job = queue[0]
    state.log(f"Starting next job: {next_job.name}")
    result = upload_and_start(next_job)

    if result:
        state.current_job = next_job.name
        completed_dir = settings.queue_dir / "completed"
        completed_dir.mkdir(exist_ok=True)
        next_job.rename(completed_dir / next_job.name)
        state.log(f"Job started successfully: {next_job.name}")
        return True

    state.log(f"Failed to start job: {next_job.name}")
    return False


# ==================== VISION ====================
def fetch_snapshot():
    try:
        r = requests.get(settings.camera_snapshot_url, timeout=10)
        if r.status_code == 200:
            img = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)
            return img
    except Exception as e:
        state.log(f"Camera error: {e}")
    return None


def analyze_bed_clear(
    reference: np.ndarray,
    current: np.ndarray,
    threshold: float = None,
):
    """Returns (is_clear, confidence, diff_percent)."""
    if threshold is None:
        threshold = settings.threshold

    if reference is None or current is None:
        return False, 0.0, 100.0

    h, w = reference.shape[:2]
    current = cv2.resize(current, (w, h))

    ref_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    cur_gray = cv2.cvtColor(current, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.GaussianBlur(ref_gray, (21, 21), 0)
    cur_gray = cv2.GaussianBlur(cur_gray, (21, 21), 0)

    diff = cv2.absdiff(ref_gray, cur_gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    non_zero = cv2.countNonZero(thresh)
    total = thresh.shape[0] * thresh.shape[1]
    pct_diff = (non_zero / total) * 100

    is_clear = pct_diff < threshold
    confidence = max(0.0, min(1.0, 1.0 - (pct_diff / (threshold * 2))))

    return is_clear, round(confidence, 3), round(pct_diff, 2)


# ==================== BACKGROUND LOOP ====================
async def auto_loop():
    """Background task that monitors printer and triggers next job."""
    while True:
        await asyncio.sleep(settings.poll_interval)

        if not state.auto_loop_enabled:
            continue

        printer_state = get_printer_status()
        state.last_status = printer_state

        if printer_state == "complete":
            # Eject should already have fired via PRINT_END_AUTO on the printer.
            if state.reference_image is None:
                state.log(
                    "No reference image — cannot auto-detect. Waiting for manual start."
                )
                continue

            snapshot = fetch_snapshot()
            if snapshot is None:
                continue

            is_clear, confidence, pct = analyze_bed_clear(
                state.reference_image, snapshot
            )

            if is_clear:
                state.clear_streak += 1
                state.log(
                    f"Bed clear detected ({state.clear_streak}/{settings.confirmation_count}) "
                    f"— conf: {confidence}, diff: {pct}%"
                )
            else:
                state.clear_streak = 0
                state.log(f"Bed occupied — diff: {pct}%, conf: {confidence}")

            if state.clear_streak >= settings.confirmation_count:
                state.clear_streak = 0
                await asyncio.sleep(5)
                # After eject, firmware may sit in complete or move to standby/ready.
                ready = get_printer_status()
                if ready in ("standby", "complete", "ready"):
                    start_next_queued_job()
                else:
                    state.log(f"Printer not ready ({ready}) — skipping auto-start")

        elif printer_state == "standby" and state.current_job is None:
            queue = sorted(settings.queue_dir.glob("*.gcode"))
            if queue:
                state.log("Printer idle with queued jobs — auto-starting")
                start_next_queued_job()


# auto_loop is started from lifespan above

# ==================== API ENDPOINTS ====================
class DetectResponse(BaseModel):
    clear: bool
    confidence: float
    diff_percent: float
    clear_streak: int
    auto_loop: bool
    status: str


@app.get("/")
def root():
    return {
        "status": "K1C Auto-Farm Detector",
        "auto_loop": state.auto_loop_enabled,
        "printer_ip": settings.ip,
    }


@app.get("/healthz")
def healthz():
    checks = {
        "reference": "pass" if state.reference_image is not None else "fail",
        "moonraker": "pass" if moonraker_get("/printer/info") else "fail",
        "camera": "pass" if fetch_snapshot() is not None else "fail",
    }
    status = "healthy" if all(v == "pass" for v in checks.values()) else "degraded"
    code = 200 if checks["moonraker"] == "pass" else 503
    return JSONResponse(
        status_code=code,
        content={"status": status, "checks": checks},
    )


@app.post("/detect", response_model=DetectResponse)
def detect(
    file: UploadFile = File(None),
    threshold: float = Form(None),
    _: None = Mutating,
):
    """Detect if bed is clear. Pass file or uses live camera."""
    if state.reference_image is None:
        return JSONResponse(
            status_code=400,
            content={"error": "No reference image set. Capture empty bed first."},
        )

    if file is not None and file.filename:
        contents = file.file.read()
        current = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    else:
        current = fetch_snapshot()

    if current is None:
        return JSONResponse(
            status_code=503, content={"error": "Cannot fetch camera image"}
        )

    use_threshold = threshold if threshold is not None else settings.threshold
    is_clear, conf, pct = analyze_bed_clear(
        state.reference_image, current, use_threshold
    )

    if is_clear:
        state.clear_streak += 1
    else:
        state.clear_streak = 0

    return DetectResponse(
        clear=is_clear,
        confidence=conf,
        diff_percent=pct,
        clear_streak=state.clear_streak,
        auto_loop=state.auto_loop_enabled,
        status=state.last_status,
    )


@app.post("/capture-reference")
def capture_reference(_: None = Mutating):
    """Capture current camera frame as the empty-bed reference."""
    img = fetch_snapshot()
    if img is None:
        return JSONResponse(status_code=503, content={"error": "Cannot fetch camera"})

    cv2.imwrite(str(settings.ref_image_path), img)
    state.reference_image = img
    state.log("Reference image captured and saved")
    return {"success": True, "path": str(settings.ref_image_path)}


@app.post("/snapshot")
def take_snapshot(_: None = Mutating):
    """Save a snapshot to captures folder."""
    img = fetch_snapshot()
    if img is None:
        return JSONResponse(status_code=503, content={"error": "Cannot fetch camera"})

    ts = time.strftime("%Y%m%d_%H%M%S")
    path = settings.captures_dir / f"snapshot_{ts}.jpg"
    cv2.imwrite(str(path), img)
    return {"success": True, "path": str(path)}


@app.get("/status")
def full_status():
    """Full printer + detector status for dashboard."""
    temps = get_temps()
    prog = get_progress()
    queue = sorted([f.name for f in settings.queue_dir.glob("*.gcode")])

    return {
        "printer_state": get_printer_status(),
        "temperatures": temps,
        "progress": prog,
        "auto_loop": state.auto_loop_enabled,
        "reference_set": state.reference_image is not None,
        "clear_streak": state.clear_streak,
        "current_job": state.current_job,
        "queue": queue,
        "queue_count": len(queue),
        "camera_url": settings.camera_stream_url,
        "snapshot_url": settings.camera_snapshot_url,
        "threshold": settings.threshold,
        "printer_ip": settings.ip,
        "log": state.log_entries[-50:],
    }


@app.post("/auto-loop/{enabled}")
def toggle_auto_loop(enabled: bool, _: None = Mutating):
    state.auto_loop_enabled = enabled
    state.log(f"Auto-loop {'ENABLED' if enabled else 'DISABLED'}")
    return {"auto_loop": enabled}


@app.post("/trigger-eject")
def trigger_eject(_: None = Mutating):
    """Manually trigger the FORCE_EJECT macro."""
    result = moonraker_post(
        "/printer/gcode/script", json_data={"script": "FORCE_EJECT"}
    )
    state.log("Manual eject triggered")
    return {"success": True, "moonraker_response": result}


@app.post("/emergency-stop")
def emergency_stop(_: None = Mutating):
    result = moonraker_post("/printer/emergency_stop")
    state.log("EMERGENCY STOP triggered")
    return {"success": True, "moonraker_response": result}


@app.post("/pause")
def pause_print(_: None = Mutating):
    result = moonraker_post("/printer/print/pause")
    state.log("Print paused")
    return {"success": True, "moonraker_response": result}


@app.post("/resume")
def resume_print(_: None = Mutating):
    result = moonraker_post("/printer/print/resume")
    state.log("Print resumed")
    return {"success": True, "moonraker_response": result}


@app.post("/cancel")
def cancel_print(_: None = Mutating):
    result = moonraker_post("/printer/print/cancel")
    state.log("Print cancelled")
    return {"success": True, "moonraker_response": result}


@app.post("/upload")
def upload_gcode(file: UploadFile = File(...), _: None = Mutating):
    """Upload a gcode file to the queue directory."""
    if not file.filename or not file.filename.endswith(".gcode"):
        return JSONResponse(
            status_code=400, content={"error": "Only .gcode files allowed"}
        )

    path = settings.queue_dir / file.filename
    with open(path, "wb") as f:
        f.write(file.file.read())

    state.log(f"Queued: {file.filename}")
    return {"success": True, "filename": file.filename, "queue_path": str(path)}


@app.delete("/queue/{filename}")
def remove_from_queue(filename: str, _: None = Mutating):
    path = settings.queue_dir / filename
    if path.exists() and path.parent.resolve() == settings.queue_dir.resolve():
        path.unlink()
        state.log(f"Removed from queue: {filename}")
        return {"success": True}
    return JSONResponse(status_code=404, content={"error": "File not found"})


@app.post("/start-job/{filename}")
def start_job(filename: str, _: None = Mutating):
    """Manually start a specific queued job."""
    path = settings.queue_dir / filename
    if not path.exists():
        return JSONResponse(
            status_code=404, content={"error": "File not found in queue"}
        )

    result = upload_and_start(path)
    if result:
        state.current_job = filename
        completed_dir = settings.queue_dir / "completed"
        completed_dir.mkdir(exist_ok=True)
        path.rename(completed_dir / filename)
        state.log(f"Manually started: {filename}")
        return {"success": True, "job": filename}
    return JSONResponse(status_code=500, content={"error": "Failed to start job"})


@app.get("/logs")
def get_logs(lines: int = 50):
    return {"logs": state.log_entries[-lines:]}


# ==================== MAIN ====================
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.environ.get("K1C_HOST", settings.host),
        port=int(os.environ.get("K1C_PORT", settings.port)),
        log_level="info",
    )
