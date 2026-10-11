#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26811.py BASE_ROOT CANDIDATE_ROOT')
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
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(p): return sha_bytes(p.read_bytes())
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
changed={p for p in a if a[p]!=c[p]}; need(changed==MOD,f'modified allowlist mismatch {sorted(changed)}')
print('PASS 26811 authority-seeded scope: 1782 -> 1782, exactly 3 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726811' in v and 'VERSION_BUILD=26811' in v,'version')
print('PASS 26811 version 0.9726811 / 26811')
need(sha(BASE/VGN)==sha(CAND/VGN),'successful 26810 VGN bytes changed')
for rel in DNG: need(sha(BASE/rel)==sha(CAND/rel),f'DNG protected bytes changed: {rel}')
print('PASS 26811 VGN/DNG ownership protected byte-identical to successful 26810')
s=(CAND/STACK).read_text()
for token in ('IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER','IRIS_26811_RESOLVE_BOUNDARY_SUMMARY','IRIS_26811_RESOLVE_BOUNDARY_COORD','IRIS_26811_RETAIN_COMPLETED_NORMAL_CHROMA_FOR_RESOLVE_PROVENANCE','IRIS_26809_RESOLVE_RGB_HUE_PROBE'):
    need(token in s,f'26811 diagnostic owner missing {token}')
need('IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER' not in s,'failed 26810 IQ owner survived')
need(s.count('IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER')==1,'26811 provenance owner duplicate')
need(all(x in s for x in ('newGreenCyan','amplifiedGreenCyan','newMagenta','amplifiedMagenta','hueRotation','ALL_4_CFA_PHASES_QUARTER','meanAbsLumaDelta','newGreenCyanPhase','newMagentaPhase')),'boundary classifications incomplete')
need(all(x in s for x in ('completedNormalRgBg=','completedNormalOppY=','validityRecoveredWeight=','accumulatedSupport=','phase=','cfaPattern=','normalFrames=','longFrames=')),'coordinate provenance incomplete')
canon=s
start=canon.index('            /* IRIS_26811_RETAIN_COMPLETED_NORMAL_CHROMA_FOR_RESOLVE_PROVENANCE')
end=canon.index('            /* IRIS_26545_SABRE_MEASURED_SUPPORT',start)
old_release='''            if (normalChromaConsensus26790 != 0) {
                releaseOwnedTexture(
                    normalChromaConsensus26790,
                    "26790 completed NORMAL chroma consensus after all LONG merges",
                )
                normalChromaConsensus26790 = 0
            }

'''
canon=canon[:start]+old_release+canon[end:]
start=canon.index('    /* IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER')
end=canon.index('    private fun createSabreRgbChromaPostprocessor()',start)
canon=canon[:start]+canon[end:]
start=canon.index('            logSabreResolveBoundaryProvenance26811(')
end=canon.index('            LargeDirectBuffer.free(sabreAccumulatedReadback)',start)
canon=canon[:start]+canon[end:]
need(sha_bytes(canon.encode())=='0ea21cb6c8f5fd5468319df5aaea2576b5e0b75111dff29f09e9348a4f4894fa','stacker does not canonicalize to exact successful 26809 pre-26810 IQ bytes')
print('PASS 26811 IQ rollback: removing diagnostic-only 26811 blocks yields exact successful 26809 stacker SHA-256')
bf=(BASE/GALLERY).read_text(); f=(CAND/GALLERY).read_text()
onpause=f[f.index('    public void onPause() {'):f.index('    @SuppressWarnings("deprecation")',f.index('    public void onPause() {'))]
base_onpause=bf[bf.index('    public void onPause() {'):bf.index('    @SuppressWarnings("deprecation")',bf.index('    public void onPause() {'))]
need(onpause==base_onpause and 'IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS' in onpause,'26808 pause/no-gear behavior changed')
launch=f[f.index('    public void launchGallery() {'):f.index('\n    public void launchSettings()',f.index('    public void launchGallery() {'))]
for token in ('IRIS_26811_DIRECT_EXACT_CAPTURE_VIEW_OWNER','getLatestImageUri()','getContentResolver().getType(exactItem)','setDataAndType(exactItem, mime)','FLAG_GRANT_READ_URI_PERMISSION','resolveActivity','authority=','row=','resolvedComponent=','chooser=false'):
    need(token in launch,f'gallery direct exact-item contract missing {token}')
need('Intent.createChooser' not in launch,'chooser must be retired from exact-item launch')
need('startActivity(galleryIntent, null)' in launch,'direct ACTION_VIEW launch missing')
need('IRIS_26811_CAPTURE_MEDIASTORE_URI_READY' in f and 'getContentResolver().getType(uri)' in f,'scanner provenance logging missing')
canon=f
ci=canon.index('    public void launchGallery() {'); cj=canon.index('\n    public void launchSettings()',ci)
bi=bf.index('    public void launchGallery() {'); bj=bf.index('\n    public void launchSettings()',bi)
canon=canon[:ci]+bf[bi:bj]+canon[cj:]
need(canon==bf,'CameraFragment changed outside launchGallery/scanner helper block')
print('PASS 26811 gallery: exact MediaStore item + actual MIME + direct ACTION_VIEW; 26808 pause owner byte-identical')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26811 protected runtime: 1779 files byte-invariant')
