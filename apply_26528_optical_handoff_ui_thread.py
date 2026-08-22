#!/usr/bin/env python3
from __future__ import annotations
import argparse, difflib, hashlib
from pathlib import Path

CAP = "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
BASE_SHA = "7d1657f8d10048e8f4381e020c9d7ce1ea9a2e362518887ad774106006a33578"
TARGET_SHA = "b702d150b14cd66f8bd37dab42502815a2c41f21c30004ec75dd7d8920e1bb08"
FWD_SHA = "b2c269cf140ae1e6b8178fdfbf9b3b6ca8991740a26c24806e5edf3413131126"
ROLLBACK_SHA = "9bb697e6a8a1dab7e240f7c9c94cdcab005880151650f56f2a19180955899883"

OLD = '''        Runnable restart = () -> {\n            if (generation != mIrisZoomCurtainGeneration) return;\n            processExecutor.execute(this::restartCamera);\n        };\n'''
NEW = '''        /* IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART\n         * restartCamera() historically runs from CameraUIController / ScaleGestureDetector on\n         * the main thread and directly touches UI-owned preview state. 26527 moved it onto\n         * processExecutor behind the curtain, violating that contract and crashing at each\n         * optical boundary. Always marshal the actual restart back to the Activity main thread.\n         */\n        Runnable restart = () -> activity.runOnUiThread(() -> {\n            if (generation != mIrisZoomCurtainGeneration) return;\n            Log.i(TAG, "IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART generation="\n                    + generation + " thread=" + Thread.currentThread().getName());\n            restartCamera();\n        });\n'''

def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())

def norm(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def transform(src: str) -> str:
    s = norm(src)
    if s.count(OLD) != 1:
        raise AssertionError(f"26528 exact worker-dispatch anchor count={s.count(OLD)} expected=1")
    out = s.replace(OLD, NEW, 1)
    if "processExecutor.execute(this::restartCamera)" in out:
        raise AssertionError("26527 worker-thread restart dispatch survived")
    if out.count("IRIS_26528_OPTICAL_HANDOFF_UI_THREAD_RESTART") != 2:
        raise AssertionError("26528 UI-thread restart marker/log count drift")
    return out

def unified(old: str, new: str, reverse: bool=False) -> str:
    a,b = (new,old) if reverse else (old,new)
    return ''.join(difflib.unified_diff(
        a.splitlines(True), b.splitlines(True),
        fromfile='a/'+CAP, tofile='b/'+CAP))

def write_hash(path: Path, digest: str) -> None:
    path.write_text(f"{digest}  {path.name.removesuffix('.sha256')}\n", encoding="utf-8")

def self_test() -> None:
    synthetic = "HEAD\n" + OLD + "TAIL\n"
    out = transform(synthetic)
    assert NEW in out and OLD not in out
    try:
        transform(synthetic.replace("processExecutor.execute(this::restartCamera);", "restartCamera();"))
    except AssertionError:
        pass
    else:
        raise AssertionError("negative predecessor-drift self-test did not stop")
    print("PASS: 26528 transformer self-test + negative predecessor drift")

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", type=Path)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--patch-out", type=Path)
    ap.add_argument("--patch-sha-out", type=Path)
    ap.add_argument("--rollback-out", type=Path)
    ap.add_argument("--rollback-sha-out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    a=ap.parse_args()
    if a.self_test:
        self_test(); return
    if a.root is None: raise SystemExit("root required")
    p=a.root/CAP
    if not p.is_file(): raise SystemExit("missing "+CAP)
    raw=p.read_bytes()
    if sha_bytes(raw) != BASE_SHA:
        raise SystemExit("successful-26527 CaptureController SHA drift")
    old=norm(raw.decode("utf-8")); new=transform(old)
    if sha_bytes(new.encode("utf-8")) != TARGET_SHA:
        raise SystemExit("26528 target CaptureController SHA drift")
    fwd=unified(old,new); rev=unified(old,new,True)
    if sha_bytes(fwd.encode()) != FWD_SHA: raise SystemExit("26528 forward patch SHA drift")
    if sha_bytes(rev.encode()) != ROLLBACK_SHA: raise SystemExit("26528 rollback patch SHA drift")
    if a.patch_out:
        a.patch_out.write_text(fwd,encoding="utf-8")
    if a.patch_sha_out:
        a.patch_sha_out.write_text(f"{FWD_SHA}  {a.patch_out.name}\n",encoding="utf-8")
    if a.rollback_out:
        a.rollback_out.write_text(rev,encoding="utf-8")
    if a.rollback_sha_out:
        a.rollback_sha_out.write_text(f"{ROLLBACK_SHA}  {a.rollback_out.name}\n",encoding="utf-8")
    print("PASS: 26528 complete transform resolved in memory")
    if not a.check_only:
        p.write_text(new,encoding="utf-8")
        print("PASS: 26528 one-owner transform applied")

if __name__ == "__main__": main()
