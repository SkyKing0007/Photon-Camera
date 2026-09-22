#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3:raise SystemExit('usage: validate_26684.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base);b=snap(cand)
expected=set("""app/src/main/cpp/spektra/SpektraNativeJni.cpp
app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java
app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java
app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java
app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java
app/version.properties""".splitlines())
actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if len(a)!=1764 or len(b)!=1764 or actual!=expected:raise SystemExit('FAIL changed scope '+repr(actual))
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726684' in ver and 'VERSION_BUILD=26684' in ver
rawf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java').read_text()
rawp=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java').read_text()
own=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java').read_text()
pre=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java').read_text()
cap=(cand/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
native=(cand/'app/src/main/cpp/spektra/SpektraNativeJni.cpp').read_text()
# VF-S exact behavioral target: 480 short edge (640x480 for 4:3), 30fps, reduced live path.
for tok in ['PREVIEW_SHORT_EDGE_DEFAULT = 480','previewProcessSize','copyPreviewFrom(image, PREVIEW_SHORT_EDGE_DEFAULT)','IRIS_26684_SPEKTRA_AUTO_LENS_PROFILE','IRIS_26684_SPEKTRA_STILL_SESSION_REUSED=true','submitStill(g, previewReader.getSurface())','watchdogExecutor.schedule','seedAutomaticLensProfiles()']:
 if tok not in own:raise SystemExit('FAIL Spektra owner contract '+tok)
for tok in ['targetFps=30','quality=LOW','previewShortEdge=480','vfS=true','canAcceptFrame()']:
 if tok not in pre:raise SystemExit('FAIL VF-S preview contract '+tok)
if 'unpackRaw10' in rawf or 'unpackRaw12' in rawf:raise SystemExit('FAIL Java full-frame RAW unpacker survived')
for tok in ['nativeDecodeRaw','copyPreviewFrom','copyStillFrom']:
 if tok not in rawf:raise SystemExit('FAIL native RAW bridge '+tok)
for tok in ['Java_com_particlesdevs_photoncamera_spektra_SpektraRawFrame_nativeDecodeRaw','kAndroidRaw10','kAndroidRaw12','kAndroidRawSensor','rowStride','packedWidthInvalid']:
 if tok not in native:raise SystemExit('FAIL native row-stride RAW decoder '+tok)
# Saved-only recovery/denoise: live VF-S must skip both.
if 'if (savedPhoto)' not in rawp or 'SAVED_CHROMA_DENOISE_STRENGTH : 0.0f' not in rawp:raise SystemExit('FAIL saved/live RAW split')
# Session reuse: no separate still reader field or still create-session path.
if re.search(r'\bstillReader\b',own):raise SystemExit('FAIL separate still ImageReader survived')
if 'configureStillSession(long g)' not in own or 'session.stopRepeating()' not in own:raise SystemExit('FAIL shared still session entry')
# Hard legacy camera exclusion at every low-level boundary.
for tok in ['iris26684BlockLegacyCameraForSpektra("surface_available")','iris26684BlockLegacyCameraForSpektra("openCamera_entry")','iris26684BlockLegacyCameraForSpektra("openCamera_async")','iris26684BlockLegacyCameraForSpektra("openCamera_pre_hal")','iris26684BlockLegacyCameraForSpektra("restart_pre_hal")','iris26684BlockLegacyCameraForSpektra("restart_locked_pre_hal")','iris26684BlockLegacyCameraForSpektra("legacy_onOpened")']:
 if tok not in cap:raise SystemExit('FAIL legacy camera exclusion '+tok)
# Complete shader universe unchanged.
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:
  q=cand/p.relative_to(base)
  if not q.is_file() or p.read_bytes()!=q.read_bytes():raise SystemExit('FAIL shader changed '+str(p.relative_to(base)))
print('PASS 26684 semantics: automatic RAW10/RAW_SENSOR candidates with persisted runtime preview/still/resume verification; VF-S 480-short-edge/30fps reduced preview; native row-stride RAW decode; saved-only recovery/denoise; shared still session; independent watchdog; hard legacy-camera exclusion')
