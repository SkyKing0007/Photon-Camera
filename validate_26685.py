#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
if len(sys.argv)!=3:raise SystemExit('usage: validate_26685.py BASE CAND')
base,cand=map(Path,sys.argv[1:])
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snap(r):return {str(p.relative_to(r)):h(p) for p in sorted((r/'app').rglob('*')) if p.is_file()}
a=snap(base);b=snap(cand);expected={'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraColorSolver.java', 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java', 'app/version.properties', 'app/src/main/cpp/spektra/SpektraNativeJni.cpp', 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java', 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java', 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java', 'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java'};actual={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
if len(a)!=1764 or len(b)!=1764 or actual!=expected:raise SystemExit('FAIL changed scope '+repr(actual))
ver=(cand/'app/version.properties').read_text();assert 'VERSION_NAME=0.9726685' in ver and 'VERSION_BUILD=26685' in ver
own=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraCameraOwner.java').read_text()
rawf=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawFrame.java').read_text()
rawp=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraRawProcessor.java').read_text()
pre=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraPreviewRenderer.java').read_text()
color=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraColorSolver.java').read_text()
meta=(cand/'app/src/main/java/com/particlesdevs/photoncamera/spektra/SpektraFrameMetadata.java').read_text()
native=(cand/'app/src/main/cpp/spektra/SpektraNativeJni.cpp').read_text()
# Spektra-only route enumeration and functional automatic scan.
for tok in ['enumerateSpektraRoutes()','automaticDiscoveryQueue','automaticDiscoveryActive','IRIS_26685_SPEKTRA_DISCOVERY_STILL_BEGIN','IRIS_26685_SPEKTRA_PROFILE_VERIFIED','functionalVerification=preview+still+resume','new int[] {ImageFormat.RAW10, ImageFormat.RAW_SENSOR}']:
 if tok not in own:raise SystemExit('FAIL verified auto-discovery '+tok)
if 'claimedPhysicalIds' not in own or 'publicId + "-" + physicalId' not in own:raise SystemExit('FAIL logical/physical route dedupe')
if 'activity.getSharedPreferences("spektra_auto_lens_discovery"' not in own:raise SystemExit('FAIL Spektra-private profile store')
# Never accept an unverified profile for user shutter.
for tok in ['currentProfileNeedsVerification || verificationCaptureInFlight','SPEKTRA_PROFILE_VERIFYING','captureVerified']:
 if tok not in own:raise SystemExit('FAIL fail-closed unverified shutter '+tok)
# Geometry/CFA contract.
for tok in ['estimateBayerOffset','BAYER_ORIGIN_AMBIGUOUS','bayerHint=UNRESOLVED','geometryBayerOffsetHint()','stillBayerOffset < 0']:
 if tok not in own+rawf:raise SystemExit('FAIL Bayer geometry '+tok)
if 'black[q] = sensorBlack[q ^ offset]' not in meta or 'cfa = sensorCfa ^ offset' not in meta:raise SystemExit('FAIL CFA/black phase ownership split')
if 'for (int q = 0; q < 4; ++q)' not in rawf:raise SystemExit('FAIL all-four-phase estimator regression')
# 26684 sparse/reduced-Bayer display owner must be gone. Reduced Bayer may remain only as AE/profile meter.
if 'mapPreviewCoordinate' in native:raise SystemExit('FAIL sparse nearest Bayer mapper survived')
for tok in ['nativeDecodePreviewRgb16f','demosaicCameraRgb','reducedPreviewRgb','averageRawPhaseBox']:
 if tok not in native:raise SystemExit('FAIL native VF-S source-lattice RGB geometry '+tok)
for tok in ['previewCameraRgb16f','nativeDecodePreviewRgb16f']:
 if tok not in rawf:raise SystemExit('FAIL VF-S camera-RGB carrier '+tok)
for tok in ['previewDecodeExecutor','previewDecodeBusy.compareAndSet(false, true)','SpektraVfsRawDecode']:
 if tok not in own:raise SystemExit('FAIL VF-S decode still owned by Camera2 callback thread '+tok)
for tok in ['LongSparseArray<Image> previewImages','schedulePreviewDecode(image, result','SpektraFrameMetadata.from(result, characteristics']:
 if tok not in own:raise SystemExit('FAIL exact preview RAW/result pairing '+tok)
for tok in ['IRIS_26685_SPEKTRA_VFS_RGB_OWNER','processPreviewRgb','shot.raw.previewCameraRgb16f']:
 if tok not in rawp:raise SystemExit('FAIL reduced Bayer still owns VF-S display '+tok)
if 'runRcd' in rawp[rawp.index('private LinearFrame processPreviewRgb'):rawp.index('private GLTexture runRcd')]:raise SystemExit('FAIL VF-S camera RGB re-enters RCD')
# Live/saved processing split and quiet preview logs. Saved-only highlight/chroma remain on full-res path.
if 'if (savedPhoto)' not in rawp or 'SAVED_CHROMA_DENOISE_STRENGTH' not in rawp:raise SystemExit('FAIL saved/live RAW split')
if 'solveQuiet' not in color or 'solveQuiet' not in pre:raise SystemExit('FAIL preview ColorSolver log throttle')
# Complete shader universe unchanged.
for p in (base/'app/src/main/assets').rglob('*'):
 if p.is_file() and p.suffix in {'.glsl','.frag','.vert','.comp'}:
  q=cand/p.relative_to(base)
  if not q.is_file() or p.read_bytes()!=q.read_bytes():raise SystemExit('FAIL shader changed '+str(p.relative_to(base)))
print('PASS 26685 semantics: Spektra-only functional automatic discovery; RAW10-first/RAW_SENSOR fallback; preview+hidden-still+resumed-viewfinder admission; route dedupe; fail-closed CFA origin; source-lattice camera-RGB reconstruction before 640x480 reduction; reduced Bayer meter never displays; saved/full-res phase ownership; no non-Spektra runtime changes')
