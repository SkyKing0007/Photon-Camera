#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26813.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
BRIDGE='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VER='app/version.properties'; MOD={STACK,SHADERS,BRIDGE,GALLERY,VER}
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
DNG={
'app/src/main/cpp/dngCreator.h','app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java'}
IQ_26809={
 STACK:'0ea21cb6c8f5fd5468319df5aaea2576b5e0b75111dff29f09e9348a4f4894fa',
 SHADERS:'b6e81869e3ceb29dd02f6d83772be41bfc53031ea1158344694ca5704a825812'}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
def block(text,start,end):
    i=text.index(start); j=text.index(end,i); return text[i:j]
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
changed={p for p in a if a[p]!=c[p]}; need(changed==MOD,f'modified allowlist mismatch {sorted(changed)}')
print('PASS 26813 authority-seeded scope: 1782 -> 1782, exactly 5 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726813' in v and 'VERSION_BUILD=26813' in v,'version')
print('PASS 26813 version 0.9726813 / 26813')
need(sha(BASE/VGN)==sha(CAND/VGN),'successful 26812 VGN bytes changed')
for rel in DNG: need(sha(BASE/rel)==sha(CAND/rel),f'DNG protected bytes changed: {rel}')
print('PASS 26813 VGN/DNG ownership protected byte-identical to successful 26812')
for rel,expected in IQ_26809.items(): need(sha(CAND/rel)==expected,f'26809 IQ byte restore mismatch: {rel}')
s=(CAND/STACK).read_text(); sh=(CAND/SHADERS).read_text()
for token in ('IRIS_26812_LONG_TRUE_LUMA_ONLY_OWNER','IRIS_26812_RESOLVE_CHROMA_CONSISTENCY_OWNER','IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER','IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER'):
    need(token not in s and token not in sh,f'post-26809 IQ owner survived: {token}')
need('IRIS_26809_RESOLVE_RGB_HUE_PROBE' in s,'26809 read-only Resolve probe missing')
print('PASS 26813 IQ baseline: exact successful 26809 stacker + Sabre shader bytes restored; 26810/26811/26812 IQ owners absent')
# Chroma no-raise is the only Bridge behavioral delta from the 26812/26809 shared bridge.
bb=(BASE/BRIDGE).read_text(); br=(CAND/BRIDGE).read_text()
marker='''            // IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER\n            // The residual-denoise output is the chroma ceiling. Protected-chroma bookkeeping may\n            // still reduce unsupported bright-edge chroma, but it may never restore/increase\n            // chroma magnitude above the denoised result. Luma and hue direction remain unchanged.\n            targetMagnitude = minOf(targetMagnitude, currentMagnitude)\n\n'''
need(br.count(marker)==1,'26813 no-raise owner count')
need(br.replace(marker,'')==bb,'Bridge changed outside exact 26813 no-raise owner')
owner_at=br.index('IRIS_26813_POST_DENOISE_CHROMA_NO_RAISE_OWNER')
raise_branch=br.index('if (targetMagnitude > currentMagnitude + 1.0e-6f)',owner_at)
need(owner_at<raise_branch,'no-raise clamp must precede all raise encoding')
print('PASS 26813 protected chroma: post-denoise magnitude is a hard ceiling; no floor restoration can raise chroma')
# Gallery: preserve exact-item mechanics, remove normal-path provenance logging, preserve 26808 pause owner.
bf=(BASE/GALLERY).read_text(); f=(CAND/GALLERY).read_text()
onpause=block(f,'    public void onPause() {','    @SuppressWarnings("deprecation")')
base_onpause=block(bf,'    public void onPause() {','    @SuppressWarnings("deprecation")')
need(onpause==base_onpause and 'IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS' in onpause,'26808 pause/no-gear behavior changed')
launch=block(f,'    public void launchGallery() {','\n    private void scanCapturedImageForGallery26810')
scan=block(f,'    private void scanCapturedImageForGallery26810','\n    public void launchSettings()')
for token in ('new Intent(Intent.ACTION_VIEW)','getLatestImageUri()','getContentResolver().getType(exactItem)','setDataAndType(exactItem, mime)','FLAG_GRANT_READ_URI_PERMISSION','setClipData','startActivity(galleryIntent, null)'):
    need(token in launch,f'gallery exact-item contract missing {token}')
for token in ('MediaScannerConnection.scanFile','cameraFragmentViewModel.updateGalleryThumb(uri)'):
    need(token in scan,f'gallery MediaStore exact-item preparation missing {token}')
need('Intent.createChooser' not in launch,'chooser must remain retired')
need('Log.d(' not in launch and 'Log.d(' not in scan,'gallery normal-path provenance logger survived')
need('IRIS_26812_GALLERY_THUMB_CLICK_ENTRY' not in f and 'IRIS_26812_GALLERY_LAUNCH_COMMIT' not in f and 'IRIS_26811_CAPTURE_MEDIASTORE_URI_READY' not in f,'gallery provenance marker survived')
print('PASS 26813 gallery: confirmed 26812 exact-item behavior retained; normal click/scan/launch provenance logging removed')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26813 protected runtime: 1777 files byte-invariant')
