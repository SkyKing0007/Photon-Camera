#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from pathlib import Path

ZOOM = "app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java"
CAPTURE = "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java"
ALLOWED = {ZOOM, CAPTURE}

PROTECTED = {
    # Proven 26525 DNG crop implementation.
    "app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java",
    "app/src/main/cpp/dngCreator.cpp",
    "app/src/main/cpp/CMakeLists.txt",

    # Active temporal / Spatial RGB image math.
    "app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt",
    "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt",
    "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt",

    # Shutter-frozen/final image geometry and IQ ownership.
    "app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/DefaultSaver.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java",
    "app/src/main/assets/shaders/motionv2/render.glsl",
    "app/src/main/assets/shaders/motionv2/gainmap.glsl",
    "app/src/main/assets/shaders/preview/main_fs.glsl",
    "app/src/main/java/com/particlesdevs/photoncamera/control/TouchFocus.java",
    "app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java",
    "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/GLPreview.java",
    "app/src/main/java/com/particlesdevs/photoncamera/ui/camera/views/viewfinder/MainRenderer.java",
}

def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

def h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def tree(root: Path):
    return {
        str(p.relative_to(root)).replace("\\", "/"): h(p)
        for p in (root / "app/src/main").rglob("*") if p.is_file()
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--patch", required=True, type=Path)
    ap.add_argument("--patch-sha", required=True, type=Path)
    ap.add_argument("--postbuild", action="store_true")
    a = ap.parse_args()

    digest = hashlib.sha256(a.patch.read_bytes()).hexdigest()
    tokens = a.patch_sha.read_text(encoding="utf-8").strip().split()
    assert tokens and tokens[0] == digest, "runtime patch SHA mismatch"

    apply_path = Path(__file__).with_name("apply_26526_combined_zoom_temporal_audit.py")
    spec = importlib.util.spec_from_file_location("iris26526_apply", apply_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    expected = mod.transformed(a.base, apply_path.parent)
    assert set(expected) == ALLOWED

    bt, ct = tree(a.base), tree(a.candidate)
    changed = {p for p in set(bt) | set(ct) if bt.get(p) != ct.get(p)}
    assert changed == ALLOWED, "26526 runtime scope mismatch: " + repr(sorted(changed))

    for rel, text in expected.items():
        assert read(a.candidate, rel) == text, "candidate differs from deterministic transform: " + rel

    for rel in PROTECTED:
        assert h(a.base / rel) == h(a.candidate / rel), "protected runtime owner changed: " + rel

    bv = read(a.base, "app/version.properties")
    cv = read(a.candidate, "app/version.properties")
    assert "VERSION_NAME=0.9726525" in bv and "VERSION_BUILD=26525" in bv
    if a.postbuild:
        assert "VERSION_NAME=0.9726526" in cv and "VERSION_BUILD=26526" in cv
    else:
        assert cv == bv, "version changed before PRE-BUILD safety proof"

    zoom = read(a.candidate, ZOOM)
    capture = read(a.candidate, CAPTURE)

    for token in (
        "IRIS_26526_SINGLE_PREVIEW_GEOMETRY_AUTHORITY",
        "IRIS_26526_TRANSACTIONAL_LENS_HANDOFF",
        "IRIS_26526_DIRECTIONAL_HANDOFF_HYSTERESIS",
        "IRIS_26526_HANDOFF_PENDING",
        "IRIS_26526_HANDOFF_COMMIT",
        "IRIS_26526_HAL_TELEMETRY_ONLY",
        "sPendingOwnerCameraId",
        "sPendingOpticalAnchor",
        "supportedHardwareMax",
        "localZoom / Math.max(1.0f, supportedHardwareMax)",
        "residualDrivenByCaptureResult=false",
    ):
        assert token in zoom, token

    # Result telemetry may update actual hardware metadata, but never residual.
    result_start = zoom.index("public static float updateFromCaptureResult")
    result_end = zoom.index("public static ZoomSnapshot snapshot", result_start)
    result_body = zoom[result_start:result_end]
    assert "sResidualSoftwareZoom = residual;" not in result_body
    assert "desiredLocal / Math.max(1.0f, actualHardware)" not in result_body

    for token in (
        "IRIS_26526_CAMERA2_SINGLE_PREVIEW_AUTHORITY",
        "IRIS_26526_SESSION_BOUND_HAL_TELEMETRY",
        "session.getDevice().getId()",
        "mCaptureSession.getDevice().getId()",
    ):
        assert token in capture, token

    assert "IrisZoomController.updateFromCaptureResult(" in capture
    assert "PhotonCamera.getSettings().mCameraID);" not in capture[
        capture.index("IRIS_26526_SESSION_BOUND_HAL_TELEMETRY"):
        capture.index("IRIS_26526_SESSION_BOUND_HAL_TELEMETRY") + 1200
    ]
    assert "iris26524PreviousResidual" not in capture
    assert "mTextureView.setSoftwareZoom(iris26524ActualResidual)" not in capture

    # The proven 26525 crop must remain exactly present.
    saver = read(a.candidate, "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java")
    dngcpp = read(a.candidate, "app/src/main/cpp/dngCreator.cpp")
    assert "dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);" in saver
    assert "IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY" in dngcpp
    assert "payloadResampled=false" in dngcpp

    print("PASS: exact two-file 26526 runtime allowlist")
    print("PASS: Camera2 single live preview geometry authority")
    print("PASS: session-bound result identity; CaptureResult cannot drive software crop")
    print("PASS: transactional pending/commit handoff + generic hysteresis")
    print("PASS: 26525 DNG 1:1 crop implementation byte-identical")
    print("PASS: MGC/Spatial RGB/temporal support image math byte-identical")

if __name__ == "__main__":
    main()
