#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: validate_26787.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26787_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
counts={
 '26787_BASE_26786_FULL_APP.sha256':1779,
 '26787_EXPECTED_CANDIDATE_FULL_APP.sha256':1779,
 '26787_PROTECTED_26786.sha256':1776,
 '26787_NATIVE_26786.sha256':819,
 '26787_VENDOR_26786.sha256':778,
 '26787_DNG_WRITER_26786.sha256':6,
 '26787_PRIOR_SOURCE_HASHES.sha256':3,
}
for n,c in counts.items():
 lines=[x for x in (ROOT/n).read_text().splitlines() if x.strip()]; assert len(lines)==c,(n,len(lines),c)
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
bu,cu=U(B),U(C); assert len(bu)==len(cu)==1779 and set(bu)==set(cu)
changed=sorted(k for k in bu if bu[k]!=cu[k]); assert changed==allowed,(changed,allowed); assert len(changed)==3
vp=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726787' in vp and 'VERSION_BUILD=26787' in vp
# Explicit protected image domains: DNG behavior and all downstream JPEG color/tone owners stay frozen.
for p in (
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
 'app/src/main/assets/shaders/motionv2/render.glsl',
 'app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
 'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
):
 assert (B/p).read_bytes()==(C/p).read_bytes(),f'protected owner changed: {p}'
SAB='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
ST='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
IR='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
def vals(root,rel):
 t=(root/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',t,re.S)}
bs,cs=vals(B,SAB),vals(C,SAB); bst,cst=vals(B,ST),vals(C,ST); bsp,csp=vals(B,SP),vals(C,SP); bi,ci=vals(B,IR),vals(C,IR)
added=sorted(set(cs)-set(bs)); removed=sorted(set(bs)-set(cs)); modified=sorted(k for k in bs.keys()&cs.keys() if bs[k]!=cs[k])
assert added==['jpegLcaPreResolve26787','jpegNeutralHighlightClamp26787'],(added,removed,modified)
assert not removed and not modified,(removed,modified)
assert bst==cst,'stacker embedded shader strings changed'; assert bsp==csp,'DNG normalize/other spatial shaders changed'; assert bi==ci,'VGN embedded shader changed'
# DNG A/B authority must remain byte-identical to successful 26786.
assert bs['normalDngMerge']==cs['normalDngMerge']
assert bsp['normalizeBayer']==csp['normalizeBayer']
for tok in ('IRIS_26786_DNG_COMBINED_AB_OPTIONS','IRIS_26786_LCA_REFERENCE_COMPATIBILITY','IRIS_26786_ONE_SIDED_DEALIAS'):
 assert tok in cs['normalDngMerge'],tok
assert 'bothGreensFullyCensored26786' in csp['normalizeBayer']
# New JPEG correction is before native Resolve and gated by the same immutable 26786 snapshot.
st=(C/ST).read_text()
for tok in (
 'IRIS_26787_SHARE_DNG_NEUTRAL_CLAMP_WITH_JPEG',
 'IRIS_26787_SHARE_DNG_LCA_WITH_JPEG',
 'IRIS_26787_JPEG_CFA_OPTIONS',
 'renderSabreJpegNeutralHighlightClamp26787',
 'renderSabreJpegLcaPreResolve26787',
 'dngOptions26786.neutralClamp',
 'dngOptions26786.lcaEnabled',
): assert tok in st,tok
# Ordering: neutral clamp -> optional SHORT fusion -> LCA -> readback/native Resolve.
pos_neutral=st.index('IRIS_26787_SHARE_DNG_NEUTRAL_CLAMP_WITH_JPEG')
pos_fusion=st.index('var fusionDecision26651',pos_neutral)
pos_lca=st.index('IRIS_26787_SHARE_DNG_LCA_WITH_JPEG',pos_fusion)
pos_read=st.index('readSabreAccumulatedRgba16f(jpegResolveCarrier26787)',pos_lca)
pos_resolve=st.index('MgcSabreResolver.resolve(',pos_read)
assert pos_neutral < pos_fusion < pos_lca < pos_read < pos_resolve
# New clamp is bounded, measured-green-validity gated, hue-free; LCA uses 26786 radial coefficients.
clamp=cs['jpegNeutralHighlightClamp26787']; lca=cs['jpegLcaPreResolve26787']
for tok in ('uValidWeights','measuredGreenValidity','source.r = min(source.r, 1.0)','source.b = min(source.b, 1.0)'): assert tok in clamp,tok
for tok in ('uKrKb26787','opticalCenter','1.0 - uKrKb26787.x','1.0 - uKrKb26787.y','center.g','center.a'): assert tok in lca,tok
for banned in ('mixG1G2','poolGreen','crossPhaseHue','desatur','saturation'):
 assert banned not in clamp and banned not in lca,banned
# Existing protected runtime owners remain present.
assert 'IRIS_26784_RESTORE_26727_VGN_RGB_OWNER' in ci['universalAdaptiveColor26561']
assert 'IRIS_26784_RETIRE_BROAD_CLIPPED_NEUTRAL' in cst['EDGE_FALSE_COLOR_SUPPRESSOR_26778']
assert 'IRIS_26781_DIRECT_POST_SHORT_RESOLVE' in st
print('PASS 26787 runtime allowlist: 3 modified + 0 added + 0 deleted; 1776 protected files unchanged')
print('PASS 26787 DNG freeze: 26786 normalDngMerge + normalizeBayer/options/settings/snapshot are byte-identical')
print('PASS 26787 JPEG ownership: neutral clamp before SHORT fusion; radial LCA after fusion; both before native Resolve')
print('PASS 26787 downstream freeze: 26778/VGN/protected chroma/tone/UHDR bytes unchanged')
print('PASS 26787 no cross-phase pooling/hue synthesis/desaturation; frame/exposure/alignment policy unchanged')
