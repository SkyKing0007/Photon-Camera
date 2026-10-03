#!/usr/bin/env python3
from pathlib import Path
import sys,hashlib
if len(sys.argv)!=3: raise SystemExit("usage: verify_26756_regressions.py BASE CANDIDATE")
base,cand=map(Path,sys.argv[1:])
bcpp=(base/"app/src/main/cpp/motionv2_jpeg444_jni.cpp").read_text(); cpp=(cand/"app/src/main/cpp/motionv2_jpeg444_jni.cpp").read_text()
bad='U ip(e,js);std::string path=ip.c?ip.c:"";e->DeleteLocalRef(js);'
assert bad in bcpp, "exact 26755 failing JNI lifetime condition missing from authority"
assert bad not in cpp, "26755 invalid DeleteLocalRef-before-ReleaseStringUTFChars survived"
assert "IRIS_26756_PLAN_B_JNI_STRING_LIFETIME_OWNER" in cpp
start=cpp.index("Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_reconstructPlanBTileDirect")
end=cpp.index("Java_com_particlesdevs_photoncamera_processing_IrisTrue2xSrNative_accumulatePlanBTile",start)
fn=cpp[start:end]
for s in ["IRIS_26756_PLAN_B_TILE0_PATH_BEGIN","IRIS_26756_PLAN_B_TILE0_PATH_UTF_ACQUIRED","IRIS_26756_PLAN_B_TILE0_PATH_UTF_RELEASED","IRIS_26756_PLAN_B_TILE0_DFT_DONE","U ip(e,js);","e->DeleteLocalRef(js);","createInputDft"]: assert s in fn,s
assert fn.index("U ip(e,js);") < fn.index("IRIS_26756_PLAN_B_TILE0_PATH_UTF_RELEASED") < fn.index("e->DeleteLocalRef(js);") < fn.index("createInputDft") < fn.index("IRIS_26756_PLAN_B_TILE0_DFT_DONE")
assert cpp.count("e->DeleteLocalRef(js);")==1
# No unrelated C++ drift: replacing the 26756 owner block with exact 26755 block must recover authority bytes.
old='        for(int j=0;j<L;j++){if(deadline.expired())return JNI_FALSE;auto js=(jstring)e->GetObjectArrayElement(paths,j);if(!js)return JNI_FALSE;U ip(e,js);std::string path=ip.c?ip.c:"";e->DeleteLocalRef(js);if(path.empty())return JNI_FALSE;iris26752planb::MapFile lm;if(!lm.openExisting(path.c_str(),inPix*sizeof(float),false))return JNI_FALSE;if(!iris26752planb::createInputDft((const float*)lm.ptr,observations.data()+(size_t)j*inPix,nx,ny,Nx,Ny,dx[(size_t)j],dy[(size_t)j],maxAbsDx,maxAbsDy,inW,inH,workers,&deadline))return JNI_FALSE;}'
mark='        /* IRIS_26756_PLAN_B_JNI_STRING_LIFETIME_OWNER'
a=cpp.index(mark); b=cpp.index('        std::vector<iris26752planb::C*>inputs;',a)
neutral=cpp[:a]+old+'\n'+cpp[b:]
assert neutral==bcpp, "unrelated native C++ drift beyond the JNI lifetime correction"
# Preserve the successful 26755 RAW-lifetime/solver-bound implementation byte-for-byte.
for rel in [
 "app/src/main/java/com/hinnka/mycamera/model/SafeImage.kt",
 "app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt",
 "app/src/main/java/com/hinnka/mycamera/processor/RawStackFrameCompat.kt",
 "app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java",
 "app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt",
 "app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java",
]: assert hashlib.sha256((base/rel).read_bytes()).digest()==hashlib.sha256((cand/rel).read_bytes()).digest(),rel
kt=(cand/"app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt").read_text()
for s in ["IRIS_26755_PLAN_B_RAW_LIFETIME_OWNER","IRIS_26755_PLAN_B_MEMORY_BEFORE_RAW_RELEASE","IRIS_26755_PLAN_B_MEMORY_AFTER_RAW_RELEASE","IRIS_26755_PLAN_B_TILE0_NATIVE_BEGIN","IRIS_26755_PLAN_B_TILE0_NATIVE_DONE","PLAN_B_MAX_MEMORY_BYTES_26753 = 32L * 1024L * 1024L","intArrayOf(512, 384, 256, 192, 128)","referencePhysicalCameraId","ipolSpectralEnhancement=true","fixedFrameCount=true","directNativeGrid=true","secondScaler=false"]: assert s in kt,s
zoom=(cand/"app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java").read_text(); assert "LOCAL_MAX_ZOOM = 30.0f" in zoom and "anchor * LOCAL_MAX_ZOOM" in zoom and "localZoom / hardwareZoom" in zoom
bs={p.relative_to(base/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (base/"app/src/main/assets/shaders").rglob("*") if p.is_file()}; cs={p.relative_to(cand/"app").as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (cand/"app/src/main/assets/shaders").rglob("*") if p.is_file()}; assert bs==cs and len(bs)==271
print("PASS 26756 regressions: exact 26755 fatal JNI lifetime condition removed; UTF released before local-ref deletion; minimal tile0 proof telemetry; no unrelated C++ drift; 26755 RAW lifetime/IPOL/zoom/IQ/DNG/UHDR preserved")
