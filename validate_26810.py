#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26810.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VER='app/version.properties'; MOD={STACK,GALLERY,VER}
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
DNG={
'app/src/main/cpp/dngCreator.h','app/src/main/cpp/deps/tiny_dng_writer.h','app/src/main/cpp/dngCreator.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/DngCreator.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2DngColorShadow.java'}
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
changed={p for p in a if a[p]!=c[p]}; need(changed==MOD,f'modified allowlist mismatch {sorted(changed)}')
print('PASS 26810 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726810' in v and 'VERSION_BUILD=26810' in v,'version')
print('PASS 26810 version 0.9726810 / 26810')
# VGN and all DNG/native/vendor logic are protected, not new color authorities.
need(sha(BASE/VGN)==sha(CAND/VGN),'26809 successful VGN bytes changed')
for rel in DNG: need(sha(BASE/rel)==sha(CAND/rel),f'DNG protected bytes changed: {rel}')
print('PASS 26810 VGN/DNG ownership protected byte-identical to successful 26809')
# Stacker may change only: host stats function, one runtime log line, and EDGE_FALSE_COLOR shader.
bs=(BASE/STACK).read_text(); s=(CAND/STACK).read_text()
for token in ('IRIS_26809_RESOLVE_RGB_HUE_PROBE','IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER','rawValidityOwner=IRIS_26614','failed26805RgbAuthority=false'):
    need(token in s,f'stacker owner/provenance missing {token}')
need(s.count('IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER')==2,'26810 owner must appear exactly shader+runtime log')
need('hueSpecific=false' in s,'hue-independent proof missing')
need('lumaPreservedExact=true' in s,'exact luma proof missing')
need('IRIS_26805_PRE_RESOLVE' not in s or 'rejected26805PreResolveRgbAuthority=false' not in s, 'failed 26805 authority unexpectedly revived')
# Canonicalize allowed blocks back to exact 26809.
def block(text,start,end):
    i=text.index(start); j=text.index(end,i); return i,j,text[i:j]
def replace_block(cur,base,start,end):
    ci,cj,_=block(cur,start,end); _,_,bb=block(base,start,end); return cur[:ci]+bb+cur[cj:]
canon=s
# Remove exactly the new runtime telemetry line.
logline='                        PLog.i(SABRE_TAG, "IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER candidateGt05=${counts26778[5]} correctedPass1=${counts26778[6]} correctedPass2=${counts26778[7]} neutralTargets=${counts26778[8]} supportedParentTargets=${counts26778[9]} hueSpecific=false rawValidityOwner=IRIS_26614 preVgn=true lumaPreservedExact=true fixedStrength=false failed26805RgbAuthority=false")\n'
need(canon.count(logline)==1,'26810 runtime telemetry line mismatch'); canon=canon.replace(logline,'')
canon=replace_block(canon,bs,'    private fun runEdgeFalseColorSuppressor26778(', '    private fun renderSabreRgb16ToFloat(')
canon=replace_block(canon,bs,'    private val EDGE_FALSE_COLOR_SUPPRESSOR_26778 = """', '    private companion object {')
need(canon==bs,'stacker changed outside exact 26810 edge false-color owner/host telemetry blocks')
print('PASS 26810 stacker scope: 26809 probe retained; only edge owner/host stats modified')
# Shader semantic contract.
start=s.index('    private val EDGE_FALSE_COLOR_SUPPRESSOR_26778 = """'); end=s.index('    private companion object {',start); sh=s[start:end]
for token in ('channelValidity26782','invalidChannel26810','channelDeficit26810','far3Parent26810','supportedColorVeto26810','saturatedColorVeto26810','targetChroma26810','unsupportedW26810'):
    need(token in sh,f'26810 shader evidence missing {token}')
for bad in ('if (centerC.g','greenHue','cyanHue','isGreen26810'):
    need(bad not in sh,f'hue-specific suppression forbidden: {bad}')
need('float y0 = lumaOf(lin0);' in sh and 'rgb1 *= (y1 > 1e-8) ? (y0 / y1) : 1.0;' in sh,'exact luma restoration changed')
need('correctedC = mix(correctedC, medianC, w26778);' in sh and 'correctedC = mix(correctedC, materialBaseline26788, coherentW);' in sh,'inherited 26778/26788 paths not preserved')
print('PASS 26810 unsupported-chroma semantics: CFA-validity + supported parent, hue-independent, exact luma restore, inherited cleanup preserved')
# Gallery: exact item first; MediaStore scanner replaces temporary FileProvider URI; 26808 onPause stays untouched.
bf=(BASE/GALLERY).read_text(); f=(CAND/GALLERY).read_text()
onpause=f[f.index('    public void onPause() {'):f.index('    @SuppressWarnings("deprecation")',f.index('    public void onPause() {'))]
base_onpause=bf[bf.index('    public void onPause() {'):bf.index('    @SuppressWarnings("deprecation")',bf.index('    public void onPause() {'))]
need(onpause==base_onpause and 'IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS' in onpause,'26808 pause/no-gear behavior changed')
launch_start=f.index('    public void launchGallery() {'); launch_end=f.index('\n    public void launchSettings()',launch_start); launch=f[launch_start:launch_end]
for token in ('IRIS_26810_EXACT_CAPTURE_VIEW_OWNER','getLatestImageUri()','setDataAndType(exactItem, "image/*")','FLAG_GRANT_READ_URI_PERMISSION','ClipData.newRawUri','MediaScannerConnection.scanFile','IRIS_26810_CAPTURE_MEDIASTORE_URI_READY'):
    need(token in launch or token in f,f'gallery exact-item contract missing {token}')
need(launch.index('setDataAndType(exactItem, "image/*")') < launch.index('MediaStore.Images.Media.EXTERNAL_CONTENT_URI'),'collection must be fallback after exact item')
save_start=f.index('        public void notifyImageSavedStatus(boolean saved, Path savedFilePath) {'); save_end=f.index('\n        @Override\n        public void onProcessingError',save_start); save=f[save_start:save_end]
need('cameraFragmentViewModel.updateGalleryThumb(imageUri);' in save and 'scanCapturedImageForGallery26810(savedFilePath);' in save,'capture URI publication ordering missing')
need(save.index('updateGalleryThumb(imageUri)') < save.index('scanCapturedImageForGallery26810(savedFilePath)'),'FileProvider fallback must precede asynchronous MediaStore replacement')
# Canonicalize allowed gallery blocks + imports and prove all else byte-identical.
canon=f.replace('import android.content.ClipData;\n','').replace('import android.media.MediaScannerConnection;\n','')
ci=canon.index('    public void launchGallery() {'); cj=canon.index('\n    public void launchSettings()',ci)
bi=bf.index('    public void launchGallery() {'); bj=bf.index('\n    public void launchSettings()',bi)
canon=canon[:ci]+bf[bi:bj]+canon[cj:]
ci=canon.index('        public void notifyImageSavedStatus(boolean saved, Path savedFilePath) {'); cj=canon.index('\n        @Override\n        public void onProcessingError',ci)
bi=bf.index('        public void notifyImageSavedStatus(boolean saved, Path savedFilePath) {'); bj=bf.index('\n        @Override\n        public void onProcessingError',bi)
canon=canon[:ci]+bf[bi:bj]+canon[cj:]
need(canon==bf,'CameraFragment changed outside exact item/scanner owner + imports')
print('PASS 26810 gallery: exact captured item first, exact MediaStore URI after scan, collection fallback only, 26808 pause owner byte-identical')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26810 protected runtime: 1779 files byte-invariant')
