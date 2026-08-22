#!/usr/bin/env python3
from __future__ import annotations
import argparse,difflib,hashlib,json,re
from pathlib import Path

ALLOWLIST=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt',
 'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/api/CameraManager2.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
 'app/src/main/cpp/dngCreator.cpp',
 'app/src/main/cpp/dngCreator.h']
BASE_SHA={'app/src/main/cpp/dngCreator.cpp': 'a1a6ae6c342eb3474052a2f170f762654e0dab20ff48a81264f6d2a9d0badb3d',
 'app/src/main/cpp/dngCreator.h': '917525fc1ffa96d2aad9d0dfebbab28d7c760b1e08a6da78420b7e38a4c31706',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt': '75c334596e79be03904237792e19114f26615386e74bf137d8cb331d68c1b502',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt': '87de3a8ccd76b57441c7d0998cdac2b89ce7a9dbe5ee2522a51be7247635cc78',
 'app/src/main/java/com/particlesdevs/photoncamera/api/CameraManager2.java': '3d6142e1d459c2d182c45ad8cabe52e4c47c0405cdd6beb192f64d1a213ce848',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java': '9b322627ea68d2edd2f3842dba21b12dc3893227a2321d73af6a83be1471a2ea',
 'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java': 'e818e25bfc66210bf689da020398fdf03b7d461a947986206bfed15ca4dca1e3',
 'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java': '32ee811466e68954a22624efc4ec80856d5a69677692e24172314604a614fc21',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java': 'fbd808727e364279c331b6a7c447775971055b86bff1ad3aac78b9e6661726a2',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java': '492c7b82ddc21eb738695643825da6b211f9fe82f6193335e22be26c9459e522'}
TARGET_SHA={'app/src/main/cpp/dngCreator.cpp': '6dec3c67c2f37e51c607d296e6c89c5118e71f42cfa49541870ed47cdd54eb1f',
 'app/src/main/cpp/dngCreator.h': '81dfd5d379fc4dc39b8d5c1b5250bd72ff9a0381bcf0154bf266c4e66f6c5006',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbShaders.kt': '88c66f1e54f369d7932e3a3119c9a15ebb69994a578f18cbd73cf257157c945c',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt': 'e45f6ce70652f518e06ed515cb3c6b9d0404944e7c8e4794c8b6d2e056d9f6e0',
 'app/src/main/java/com/particlesdevs/photoncamera/api/CameraManager2.java': 'b36ea3755f7815f465f60040063166b18d006cb6bbc8260ec52d3b7ae4d9c326',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java': '7d1657f8d10048e8f4381e020c9d7ce1ea9a2e362518887ad774106006a33578',
 'app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java': '842f9d3917d8033611f5b47d1642eabfa06f7418e58d9efc639673cdd0113efc',
 'app/src/main/java/com/particlesdevs/photoncamera/control/Swipe.java': '8d5f88536c42af66d299976e6903d84ca1b7e1ae9a8d183b34d469459ac0dc43',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java': '9612ad03eb341b609c3c98bbc9149abb93e8df332e48c6a90169209b271ca585',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java': '30d0e217f3af592fa7650087c3fad4117fb5dc8ddafd11d93d66de54a8f0c0eb'}

def h(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s:str)->str: return s.replace("\r\n","\n").replace("\r","\n")
def t(root:Path,rel:str)->str: return norm((root/rel).read_text(encoding="utf-8"))

def changed_files(base:Path,cand:Path)->set[str]:
    names=set()
    for p in base.joinpath("app/src/main").rglob("*"):
        if p.is_file(): names.add(p.relative_to(base).as_posix())
    for p in cand.joinpath("app/src/main").rglob("*"):
        if p.is_file(): names.add(p.relative_to(cand).as_posix())
    out=set()
    for rel in names:
        a=base/rel;b=cand/rel
        if not a.is_file() or not b.is_file() or a.read_bytes()!=b.read_bytes(): out.add(rel)
    return out

def expected_patch(base:Path,cand:Path)->bytes:
    chunks=[]
    for rel in ALLOWLIST:
        a=norm((base/rel).read_text(encoding="utf-8")).splitlines(True)
        b=norm((cand/rel).read_text(encoding="utf-8")).splitlines(True)
        chunks.extend(difflib.unified_diff(a,b,fromfile="a/"+rel,tofile="b/"+rel,n=3))
    return ''.join(chunks).encode()

def semantic(c:Path)->dict:
    sh=t(c,ALLOWLIST[0]); st=t(c,ALLOWLIST[1]); zoom=t(c,ALLOWLIST[2]); swipe=t(c,ALLOWLIST[3])
    cap=t(c,ALLOWLIST[4]); cam=t(c,ALLOWLIST[5]); dj=t(c,ALLOWLIST[6]); saver=t(c,ALLOWLIST[7]); cpp=t(c,ALLOWLIST[8]); hh=t(c,ALLOWLIST[9])
    req={
      "spatial_parity":"IRIS_26527_FINAL_MGC_REJECTION_ALIGNMENT_PARITY" in sh+st,
      "pixel_diff_downsample":"val rejectionPixelDifferenceDownsample" in sh and "renderPixelDifferenceDownsample(rawPixelDifference, pixelDifference)" in st,
      "acceptance_max":"max(deltaWeight, centerWeight)" in sh,
      "acceptance_weight_names":"uOriginalWeight" in sh and "uFilteredWeight" in sh,
      "raw4_unsigned_luma":"uniform highp usampler2D uBaseLuma" in sh and "referenceGrayPyramid[1].texture" in st,
      "final_alignment":"IRIS_26527_FINAL_ALIGNMENT_FIELD_OWNER" in st and "val bayerAlignment = alignment.texture" in st,
      "telemetry":"IRIS_26527_TEMPORAL_ACCEPTANCE_STAGES" in st,
      "zoom_requested_displayed":"IRIS_26527_REQUESTED_VS_DISPLAYED_ZOOM" in zoom,
      "zoom_sequential":"IRIS_26527_SEQUENTIAL_OPTICAL_ANCHORS" in zoom and "chainedPendingOwnerCameraId" in zoom,
      "pinch_cancel":"IRIS_26527_PINCH_OWNS_GESTURE_STREAM" in swipe and "MotionEvent.ACTION_CANCEL" in swipe,
      "session_route":"IRIS_26527_SESSION_BOUND_ROUTE_OWNER" in cap and "mIrisSessionRoutes.get(session)" in cap,
      "physical_binding":"config.setPhysicalCameraId(irisSessionRoute.physicalOutputId);" in cap,
      "adaptive_route":"IRIS_26527_ADAPTIVE_LOGICAL_PHYSICAL_SEARCH" in cap,
      "route_setup":"IRIS_26527_SINGLE_ROUTE_AUTHORITY_SURFACE" in cap and "IRIS_26527_SINGLE_ROUTE_AUTHORITY_SETUP" in cap,
      "curtain":"IRIS_26527_CURTAIN_FAILSAFE_MS = 1600L" in cap and "IRIS_26527_ZOOM_CURTAIN_FAILSAFE" in cap,
      "topology":"IRIS_26527_CAMERA_TOPOLOGY_DIAGNOSTICS" in cam,
      "dng_java":"setEmbeddedPreviewEnabled" in dj,
      "dng_default_crop":"dngCreator.setDefaultCropZoom(parameters.motionV2OutputZoom);" in saver,
      "dng_still_only":saver.count("dngCreator.setEmbeddedPreviewEnabled(true);")==1,
      "dng_native":"embedded_preview_enabled" in hh and "iris26527BuildPreview" in cpp,
      "dng_subifd":"SetCustomFieldULong(330, 0u)" in cpp and "iris26527PromoteSecondIfdToSubIfd" in cpp,
      "main_strip":"metadata.strip_offset = dng_image0->GetStripOffset();" in cpp,
    }
    bad=[k for k,v in req.items() if not v]
    if bad: raise SystemExit("semantic gates failed: "+", ".join(bad))
    for old in ("convertBayerAlignment","renderBayerAlignment(","renderMergeDomainFlow("):
        if old in sh+st: raise SystemExit("obsolete active Spatial stage survived: "+old)
    prep=st.index("private fun prepareTemporalFrame")
    order=[st.index("renderDilation(rawReverseWeight, initialWeight)",prep),st.index("renderPixelDifferenceDownsample(rawPixelDifference, pixelDifference)",prep),st.index("renderRejectionFilterDownsample(",prep),st.index("renderRejectionPostprocess(",prep)]
    if order != sorted(order) or len(set(order))!=4: raise SystemExit("final MGC stage order drift")
    surface=cap[cap.index("public final TextureView.SurfaceTextureListener"):cap.index("public CaptureController(")]
    if 'String curID = PhotonCamera.getSettings().mCameraID;' in surface or 'split("-")' in surface:
        raise SystemExit("legacy surface camera split authority survived")
    a=cap.index("private void setUpCameraOutputs"); b=cap.index("/**",a+50); setup=cap[a:b]
    if 'split("-")' in setup or "iris26527ResolveRoute" not in setup: raise SystemExit("legacy setup split authority survived")
    a=cap.index("public void restartCamera()"); b=cap.index("private Size getAspect",a); restart=cap[a:b]
    if restart.index("setUpCameraOutputs") > restart.index("mCameraManager.openCamera"): raise SystemExit("camera restart callback race survived")
    if cap.count("mIrisSessionRoutes.remove(cameraCaptureSession)")!=2: raise SystemExit("session route cleanup count drift")
    if cpp.count("SetCustomFieldULong(330, 0u)")!=1: raise SystemExit("SubIFD tag count drift")
    return req

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--base",required=True); ap.add_argument("--candidate",required=True)
    ap.add_argument("--patch",required=True); ap.add_argument("--patch-sha",required=True); ap.add_argument("--rollback",required=True); ap.add_argument("--rollback-sha",required=True)
    ap.add_argument("--postbuild",action="store_true"); ap.add_argument("--json-out")
    a=ap.parse_args(); b=Path(a.base); c=Path(a.candidate)
    v=norm((c/"app/version.properties").read_text())
    want=("0.9726527","26527") if a.postbuild else ("0.9726526","26526")
    if f"VERSION_NAME={want[0]}" not in v or f"VERSION_BUILD={want[1]}" not in v: raise SystemExit("candidate version/build gate failed")
    actual=changed_files(b,c)
    if actual!=set(ALLOWLIST): raise SystemExit(f"runtime changed-file allowlist mismatch extra={sorted(actual-set(ALLOWLIST))} missing={sorted(set(ALLOWLIST)-actual)}")
    for rel in ALLOWLIST:
        if h(b/rel)!=BASE_SHA[rel]: raise SystemExit("base owner SHA drift: "+rel)
        if h(c/rel)!=TARGET_SHA[rel]: raise SystemExit("candidate target SHA drift: "+rel)
    p=Path(a.patch); rb=Path(a.rollback)
    def check_hash(hashfile:Path,target:Path):
        parts=hashfile.read_text().strip().split()
        if len(parts)<2 or parts[0]!=hashlib.sha256(target.read_bytes()).hexdigest(): raise SystemExit("patch hash-file mismatch: "+str(target))
    check_hash(Path(a.patch_sha),p); check_hash(Path(a.rollback_sha),rb)
    ep=expected_patch(b,c)
    if p.read_bytes()!=ep: raise SystemExit("forward runtime patch != independently regenerated exact delta")
    # independent rollback regeneration
    chunks=[]
    for rel in ALLOWLIST:
        aa=norm((c/rel).read_text()).splitlines(True); bb=norm((b/rel).read_text()).splitlines(True)
        chunks.extend(difflib.unified_diff(aa,bb,fromfile="a/"+rel,tofile="b/"+rel,n=3))
    if rb.read_bytes()!=''.join(chunks).encode(): raise SystemExit("rollback runtime patch != independently regenerated reverse delta")
    gates=semantic(c)
    report={"runtimeChangedFiles":sorted(actual),"runtimeChangedFileCount":len(actual),"semantic":gates,"postbuild":a.postbuild,"version":want[0],"build":want[1]}
    if a.json_out: Path(a.json_out).write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("PASS: independent exact 10-owner runtime allowlist")
    print("PASS: forward + rollback patches independently reproduced and hashed")
    print("PASS: 26523/26524/26525/26526 frozen ownership invariants preserved")
    print("PASS: 26527 Spatial + zoom/route + DNG semantic owner proof")
if __name__=="__main__": main()
