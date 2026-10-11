#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26812.py BASE_ROOT CANDIDATE_ROOT')
BASE,CAND=map(Path,sys.argv[1:])
STACK='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SHADERS='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
GALLERY='app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraFragment.java'
VER='app/version.properties'; MOD={STACK,SHADERS,GALLERY,VER}
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
def between(text,start,end):
    i=text.index(start); j=text.index(end,i); return text[i:j]
a,c=uni(BASE),uni(CAND)
need(len(a)==1782 and len(c)==1782,(len(a),len(c))); need(set(a)==set(c),'file universe changed')
changed={p for p in a if a[p]!=c[p]}; need(changed==MOD,f'modified allowlist mismatch {sorted(changed)}')
print('PASS 26812 authority-seeded scope: 1782 -> 1782, exactly 4 modified / 0 added / 0 deleted')
v=(CAND/VER).read_text(); need('VERSION_NAME=0.9726812' in v and 'VERSION_BUILD=26812' in v,'version')
print('PASS 26812 version 0.9726812 / 26812')
need(sha(BASE/VGN)==sha(CAND/VGN),'successful 26811 VGN bytes changed')
for rel in DNG: need(sha(BASE/rel)==sha(CAND/rel),f'DNG protected bytes changed: {rel}')
print('PASS 26812 VGN/DNG ownership protected byte-identical to successful 26811')
bs=(BASE/STACK).read_text(); s=(CAND/STACK).read_text(); sh=(CAND/SHADERS).read_text()
for token in ('IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER','IRIS_26811_RESOLVE_BOUNDARY_SUMMARY','IRIS_26811_RESOLVE_BOUNDARY_COORD','IRIS_26809_RESOLVE_RGB_HUE_PROBE'):
    need(token in s,f'26811 provenance logger missing {token}')
base_logger=between(bs,'    /* IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER','    private fun createSabreRgbChromaPostprocessor()')
cand_logger=between(s,'    /* IRIS_26811_RESOLVE_BOUNDARY_PROVENANCE_OWNER','    private fun createSabreRgbChromaPostprocessor()')
need(base_logger==cand_logger,'26811 boundary logger implementation changed')
need('IRIS_26810_UNSUPPORTED_RESOLVE_CHROMA_OWNER' not in s,'failed 26810 RGB-parent owner survived')
for token in ('IRIS_26812_LONG_TRUE_LUMA_ONLY_OWNER','longLumaAccumulator26812','longLumaOnlyOutput26812','renderSabreLongLumaScale26812','applySabreLongLumaScale26812','normalRgbDirectionPreservedExact=true','longRgbAccumulatorMutation=false','longChannelWeightMutation=false','longValidityMutation=false','scalarSupport=minRGB','lumaOnly=true'):
    need(token in s,f'26812 LONG luma-only owner missing {token}')
need('accumulatedValidity26614 = if (longLumaOnly26812) 0 else accumulatedValidity26614' in s,'LONG still writes NORMAL validity')
need('normalChromaConsensus26790 = 0' in s and 'longChromaGuard26790 = false' in s,'old LONG chroma guard still active')
need('longLumaOnlyOutput26812 = if (longLumaOnly26812) longLumaAccumulator26812 else 0' in s,'LONG scalar target routing missing')
merge_call=between(s,'                        normalChromaConsensus26790 = 0,','                    )\n                } else {')
need('frame.role == RawBurstFrameRole.SHADOW_LONG' not in merge_call,'active LONG color/chroma guard survived merge call')
for token in ('uniform int uLongLumaOnly26812','float completeSupport = min(','oColorAndRWeight = vec4(longY * completeSupport, completeSupport, 0.0, 0.0)','oWeightsGb = vec2(0.0)','oValidWeights = vec4(0.0)','IRIS_26812_LONG_TRUE_LUMA_ONLY_SCALE','IRIS_26812_LONG_TRUE_LUMA_ONLY_APPLY'):
    need(token in sh,f'26812 LONG shader contract missing {token}')
need('GLES30.glBlendFuncSeparate(' in s and 'GLES30.GL_ZERO, GLES30.GL_SRC_COLOR' in s and 'GLES30.GL_ZERO, GLES30.GL_ONE' in s,'in-place scalar RGB multiply / alpha preserve blend missing')
print('PASS 26812 LONG ownership: isolated scalar luminance evidence only; NORMAL RGB/channel weights/validity immutable')
for token in ('IRIS_26812_RESOLVE_CHROMA_CONSISTENCY_OWNER','uPreResolveRgb26812','uResolveChromaGuard26812','uFinalGains26812','constrainResolveChroma26812','newExcess','amplificationExcess','directionalAgreement','correctedC = mix(postC, preC, gate)','correctedCalc *= postY / correctedY'):
    need(token in sh or token in s,f'26812 Resolve guard missing {token}')
guard=between(sh,'        vec3 constrainResolveChroma26812','        vec3 transformOutput')
need('green' not in guard.lower(),'Resolve consistency guard became green-specific')
need('magenta' not in guard.lower(),'Resolve consistency guard became magenta-specific')
need(s.count('resolveChromaGuard26812 = true')==2,'Resolve guard must be enabled in exactly physical-HDR and VGN-normalization output transforms')
need('preResolveRgb26812 = resolveExtendedLinear26651' in s,'exact Resolve input GPU authority not bound')
need(s.index('logSabreResolveBoundaryProvenance26811(') < s.index('resolveChromaGuard26812 = true'),'26811 logger must remain before 26812 correction')
need('postResolveLumaPreserved=true' in s and 'lensShadingAfterGuard=true' in s and 'hueSpecific=false' in s,'Resolve guard ownership log incomplete')
print('PASS 26812 Resolve chroma consistency: hue-independent NEW/AMPLIFIED/HUE-ROTATED guard, exact post-Resolve luminance preserved')
bf=(BASE/GALLERY).read_text(); f=(CAND/GALLERY).read_text()
onpause=f[f.index('    public void onPause() {'):f.index('    @SuppressWarnings("deprecation")',f.index('    public void onPause() {'))]
base_onpause=bf[bf.index('    public void onPause() {'):bf.index('    @SuppressWarnings("deprecation")',bf.index('    public void onPause() {'))]
need(onpause==base_onpause and 'IRIS_26808_PAUSE_MUST_NOT_OPEN_SETTINGS' in onpause,'26808 pause/no-gear behavior changed')
launch=f[f.index('    public void launchGallery() {'):f.index('\n    public void launchSettings()',f.index('    public void launchGallery() {'))]
for token in ('IRIS_26811_DIRECT_EXACT_CAPTURE_VIEW_OWNER','getLatestImageUri()','getContentResolver().getType(exactItem)','setDataAndType(exactItem, mime)','FLAG_GRANT_READ_URI_PERMISSION','startActivity(galleryIntent, null)','IRIS_26812_GALLERY_THUMB_CLICK_ENTRY','IRIS_26812_GALLERY_LAUNCH_COMMIT','resolvedComponent=','chooser=false','launched=false','launched=true'):
    need(token in launch,f'gallery contract/provenance missing {token}')
need('Intent.createChooser' not in launch,'chooser must remain retired')
# Prove no code outside launchGallery changed from successful 26811.
ci=f.index('    public void launchGallery() {'); cj=f.index('\n    public void launchSettings()',ci)
bi=bf.index('    public void launchGallery() {'); bj=bf.index('\n    public void launchSettings()',bi)
need(f[:ci]==bf[:bi] and f[cj:]==bf[bj:],'CameraFragment changed outside launchGallery')
# Preserve all key 26811 launch semantics while only adding logging.
for token in ('new Intent(Intent.ACTION_VIEW)','getLatestImageUri()','getContentResolver().getType(exactItem)','setDataAndType(exactItem, mime)','setClipData','startActivity(galleryIntent, null)'):
    need(launch.count(token)==bf[bi:bj].count(token),f'26811 gallery semantic count changed: {token}')
print('PASS 26812 gallery: successful 26811 direct exact-item behavior unchanged; click/launch provenance added; 26808 pause owner byte-identical')
for rel in a:
    if rel in MOD: continue
    need(a[rel]==c[rel],f'unexpected protected change {rel}')
print('PASS 26812 protected runtime: 1778 files byte-invariant')
