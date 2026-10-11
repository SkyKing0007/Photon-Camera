#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26809.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
VGN='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VER='app/version.properties'; MOD={VGN,STACK,GALLERY,VER}
VGN_26807_SHA='50514a5b1aed75bf9784105c78d4d87d6d01cc4e7f9415fbb8d63e85f1e8c7f1'
def need(c,m):
    if not c: raise AssertionError(m)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(r): return {p.relative_to(r).as_posix():sha(p) for p in (r/'app').rglob('*') if p.is_file()}
a,c=uni(BASE),uni(CAND); need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
need({p for p in a if a[p]!=c[p]}==MOD,'modified allowlist mismatch')
print('PASS 26809 authority-seeded scope: 1782 -> 1782, exactly 4 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726809' in v and 'VERSION_BUILD=26809' in v,'version')
print('PASS 26809 version 0.9726809 / 26809')
# Exact 26807 VGN restoration; reject the failed 26808 local admission.
g=(CAND/VGN).read_text()
need(sha(CAND/VGN)==VGN_26807_SHA,'VGN is not exact successful 26807 bytes')
for token in ('IRIS_26806_BROAD_2D_BRIGHT_COLOR_OPT_IN','IRIS_26807_HIGHLIGHT_CLEANUP_OUTRANKS_EDGE_PROTECTION','IRIS_26807_CONTIGUOUS_HIGHLIGHT_CLEANUP_TRANSPORT','IRIS_26807_NO_DOWNSTREAM_HIGHLIGHT_CHROMA_RESURRECTION'):
    need(token in g,f'26807 owner missing {token}')
for token in ('IRIS_26808_LOCAL_HIGHLIGHT_EDGE_ADMISSION','brightNeutralCoreSum26808','localHighlightEdgeCleanupProof26808'):
    need(token not in g,f'failed 26808 IQ owner survived {token}')
need('float inheritedHighlightPermission=1.0-smoothstep(0.72,0.92,centerNormalizedY);' in g,'26807 highlight curve changed')
print('PASS 26809 IQ baseline: VGN byte-identical to successful 26807; failed 26808 local-highlight admission retired')
# Resolve logger must be at exact planar Resolve output, before any 26778/VGN carrier mutation.
s=(CAND/STACK).read_text(); bs=(BASE/STACK).read_text()
need('IRIS_26809_RESOLVE_RGB_HUE_PROBE' in s,'Resolve hue probe missing')
call='logSabreResolveHueProbe26809('
# Anchor on the production HDR stats call, then prove the immediately preceding ResolveSabre call.
stats=s.index('            logSabreResolvedRgbStats(')
resolve=s.rfind('            MgcSabreResolver.resolve(',0,stats)
need(resolve>=0,'production ResolveSabre call missing before HDR stats')
probe=s.index('            logSabreResolveHueProbe26809(', stats)
free=s.index('            LargeDirectBuffer.free(sabreAccumulatedReadback)', probe)
upload=s.index('            uploadSabreResolvedRgb16Planar(', free)
suppress=s.index('                        val counts26778 = runEdgeFalseColorSuppressor26778(', upload)
need(resolve < stats < probe < free < upload < suppress,'Resolve probe ordering incorrect')
helper_marker=s.index('     * IRIS_26809_RESOLVE_RGB_HUE_PROBE')
helper_start=s.rfind('    /**',0,helper_marker)
helper_end=s.index('    private fun createSabreRgbChromaPostprocessor()',helper_marker)
helper=s[helper_start:helper_end]
for forbidden in ('GLES30.','GLES31.','.put(', 'glBind', 'glDispatch'):
    need(forbidden not in helper,f'Resolve probe is not read-only: {forbidden}')
for token in ('samplePattern=CHECKERBOARD_HALF','cellSize=$cellSize','greenCyanPhase=','magentaPhase=','topGreenCyanCells=','topMagentaCells=','readOnly=true'):
    need(token in helper,f'Resolve probe evidence missing {token}')
# Canonicalize only the two injected blocks and prove all other stacker bytes are exact 26808.
call_block=s[stats:free]
base_stats=bs.index('            logSabreResolvedRgbStats(')
base_free=bs.index('            LargeDirectBuffer.free(sabreAccumulatedReadback)',base_stats)
base_call_block=bs[base_stats:base_free]
canon=s.replace(call_block,base_call_block).replace(s[helper_start:helper_end],'')
need(canon==bs,'stacker changed outside exact read-only Resolve probe')
print('PASS 26809 Resolve probe: exact post-Resolve/pre-26778/pre-VGN ordering; read-only; stacker otherwise byte-identical to 26808')
# Gallery keeps 26808 lifecycle fix but launches collection context, not one latest item.
f=(CAND/GALLERY).read_text(); bf=(BASE/GALLERY).read_text()
onpause=f[f.index('    public void onPause() {'):f.index('    @SuppressWarnings("deprecation")',f.index('    public void onPause() {'))]
base_onpause=bf[bf.index('    public void onPause() {'):bf.index('    @SuppressWarnings("deprecation")',bf.index('    public void onPause() {'))]
need(onpause==base_onpause,'26808 pause/no-gear fix changed')
need('IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS' in onpause,'26808 pause owner missing')
launch=f[f.index('    public void launchGallery() {'):f.index('\n    public void launchSettings()',f.index('    public void launchGallery() {'))]
need('IRIS_26809_BROWSABLE_MEDIA_COLLECTION_OWNER' in launch,'collection owner missing')
need('MediaStore.Images.Media.EXTERNAL_CONTENT_URI' in launch,'MediaStore collection URI missing')
need('Intent.createChooser(galleryIntent, null)' in launch,'chooser missing')
need('getLatestImageUri(' not in launch and 'galleryIntent.setDataAndType(latest' not in launch and 'FLAG_GRANT_READ_URI_PERMISSION' not in launch,'single-item gallery authority survived')
need('cameraFragmentBinding.getUimodel().setSettingsBarVisibility(false);' in launch,'defensive settings close missing')
# Canonicalize only launchGallery and prove all other CameraFragment bytes are exact 26808.
blaunch=bf[bf.index('    public void launchGallery() {'):bf.index('\n    public void launchSettings()',bf.index('    public void launchGallery() {'))]
need(f.replace(launch,blaunch)==bf,'CameraFragment changed outside launchGallery')
print('PASS 26809 gallery: browsable MediaStore collection chooser; successful 26808 no-gear pause owner preserved byte-identical')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26809 protected runtime: 1778 files byte-invariant')
