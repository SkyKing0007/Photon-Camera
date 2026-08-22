#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import math
from pathlib import Path

ALLOWED = {
    "app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java",
    "app/src/main/cpp/dngCreator.cpp",
    "app/src/main/cpp/CMakeLists.txt",
}
PROTECTED = {
    "app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt",
    "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt",
    "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java",
    "app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java",
    "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
    "app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java",
    "app/src/main/assets/shaders/motionv2/render.glsl",
    "app/src/main/assets/shaders/motionv2/gainmap.glsl",
    "app/src/main/assets/shaders/preview/main_fs.glsl",
}
TINYDNG_COMMIT = "857590b3997818a4ccfbb8a42dd21c76273d6837"
TINYDNG_BLOB = "624d614bf3e3bccb394ec54d1bca5bbb350859be"

def read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tree(root: Path) -> dict[str, str]:
    out = {}
    for p in (root / "app/src/main").rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("\\", "/")] = sha(p)
    return out

def crop(full_w: int, full_h: int, zoom: float):
    ox = oy = 0
    cw, ch = full_w, full_h
    z = zoom if math.isfinite(zoom) and zoom >= 1.0 else 1.0
    if z > 1.00001 and full_w >= 2 and full_h >= 2:
        cw = int(math.floor(full_w / z))
        ch = int(math.floor(full_h / z))
        max_even_w = full_w & ~1
        max_even_h = full_h & ~1
        cw = max(2, min(max_even_w, cw & ~1))
        ch = max(2, min(max_even_h, ch & ~1))
        ox = ((full_w - cw) // 2) & ~1
        oy = ((full_h - ch) // 2) & ~1
        ox = max(0, min(ox, full_w - cw))
        oy = max(0, min(oy, full_h - ch))
    return ox, oy, cw, ch

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--patch", required=True, type=Path)
    ap.add_argument("--patch-sha", required=True, type=Path)
    ap.add_argument("--postbuild", action="store_true")
    a = ap.parse_args()

    patch_digest = hashlib.sha256(a.patch.read_bytes()).hexdigest()
    manifest = a.patch_sha.read_text(encoding="utf-8").strip().split()
    assert len(manifest) >= 2 and manifest[0] == patch_digest, "runtime patch SHA mismatch"

    apply_path = Path(__file__).with_name("apply_26525_dng_zoom_parity.py")
    spec = importlib.util.spec_from_file_location("iris26525_apply_exact", apply_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    expected = mod.transformed(a.base)
    assert set(expected) == ALLOWED

    base_tree = tree(a.base)
    cand_tree = tree(a.candidate)
    changed = {p for p in set(base_tree) | set(cand_tree) if base_tree.get(p) != cand_tree.get(p)}
    assert changed == ALLOWED, "26525 runtime scope mismatch: " + repr(sorted(changed))
    for rel, expected_text in expected.items():
        assert read(a.candidate, rel) == expected_text, "candidate differs from deterministic 26525 transform: " + rel

    for rel in PROTECTED:
        assert sha(a.base / rel) == sha(a.candidate / rel), "protected imaging/zoom owner changed: " + rel

    base_version = read(a.base, "app/version.properties")
    cand_version = read(a.candidate, "app/version.properties")
    assert "VERSION_NAME=0.9726524" in base_version and "VERSION_BUILD=26524" in base_version
    if a.postbuild:
        assert "VERSION_NAME=0.9726525" in cand_version and "VERSION_BUILD=26525" in cand_version
    else:
        assert cand_version == base_version, "version changed before safety proof"

    dngj = read(a.candidate, "app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java")
    saver = read(a.candidate, "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java")
    cpp = read(a.candidate, "app/src/main/cpp/dngCreator.cpp")
    cmake = read(a.candidate, "app/src/main/cpp/CMakeLists.txt")
    params = read(a.candidate, "app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java")

    assert dngj.count("IRIS_26525_DNG_DEFAULT_CROP_ZOOM_PARITY") == 2
    assert "private native void setDefaultCropZoom(long nativePtr, double zoom);" in dngj
    assert "public void setDefaultCropZoom(double zoom)" in dngj
    assert "Double.isFinite(zoom)" in dngj

    assert saver.count("dngCreator.setDefaultCropZoom(") == 1
    marker = saver.index("IRIS_26522_NORMALIZED16_STACKED_DNG_WRITER")
    boundary = saver.index("        public static boolean saveSingleRaw(", marker)
    stacked = saver[marker:boundary]
    assert "IRIS_26523_SINGLE_METADATA=true" in stacked
    assert "dngCreator.setParameters(parameters, false, false);" in stacked
    assert "dngCreator.setDefaultCropZoom(parameters.iris26524OutputLocalZoom);" in stacked
    assert "setDefaultCropZoom(" not in saver[boundary:]
    assert "iris26524OutputLocalZoom" in params

    for token in (
        "double default_crop_zoom = 1.0;",
        "void setDefaultCropZoom(double zoom)",
        "dng_image0->SetDefaultCrop(defaultCropOrigin, defaultCropSize)",
        "cropWidth & ~1",
        "cropHeight & ~1",
        "originX = ((actualWidth - cropWidth) / 2) & ~1",
        "originY = ((actualHeight - cropHeight) / 2) & ~1",
        "payloadResampled=false",
        "Java_com_particlesdevs_photoncamera_processing_DngCreator_setDefaultCropZoom",
    ):
        assert token in cpp, token

    for token in (
        "IRIS_26525_PINNED_TINYDNG_DEFAULT_CROP",
        TINYDNG_COMMIT,
        TINYDNG_BLOB,
        "git hash-object",
        "TIFFTAG_DEFAULT_CROP_ORIGIN = 50719",
        "TIFFTAG_DEFAULT_CROP_SIZE = 50720",
        "IRIS_26525_TINYDNG_DEFAULT_CROP_API",
        "IRIS_26525_TINYDNG_DEFAULT_CROP_IMPL",
        "TIFF_LONG, 2",
    ):
        assert token in cmake, token
    assert "refs/heads/master/tiny_dng_writer.h" not in cmake

    for w, h in ((3072, 4096), (4080, 3060), (3073, 4097)):
        assert crop(w, h, 1.0) == (0, 0, w, h)
        for z in (1.01, 1.2, 2.0, 2.9, 4.0, 10.0, 20.0, 50.0):
            ox, oy, cw, ch = crop(w, h, z)
            assert cw >= 2 and ch >= 2
            assert ox >= 0 and oy >= 0 and ox + cw <= w and oy + ch <= h
            assert (ox & 1) == 0 and (oy & 1) == 0
            assert (cw & 1) == 0 and (ch & 1) == 0

    spatial = read(a.candidate, "app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt")
    render = read(a.candidate, "app/src/main/assets/shaders/motionv2/render.glsl")
    gain = read(a.candidate, "app/src/main/assets/shaders/motionv2/gainmap.glsl")
    for inherited in (
        "IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_MOMENTS",
        "IRIS_26523_DNG_FRAME_EQUIVALENT_SUPPORT_Q8",
    ):
        assert inherited in spatial
    assert "IRIS_26524_FULLSIZE_MOTION_ZOOM_RENDER" in render
    assert "IRIS_26524_UHDR_ZOOM_GEOMETRY_PARITY" in gain

    print("PASS: exact four-file deterministic 26525 DNG-only runtime delta")
    print("PASS: frozen 26524 Motion local zoom is sole stacked-DNG crop authority")
    print("PASS: centered Bayer-even DefaultCrop metadata preserves full stacked RAW payload")
    print("PASS: MGC/Spatial/JPEG/UHDR/zoom/capture/support owners are byte-identical")

if __name__ == "__main__":
    main()
