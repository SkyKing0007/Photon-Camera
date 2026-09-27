#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
if len(sys.argv)!=3: raise SystemExit('usage: verify_26719_regressions.py BASE26718R1 CAND26719')
b,c=map(Path,sys.argv[1:]); pkg=Path(__file__).resolve().parent
def H(r): return {'app/'+str(p.relative_to(r/'app')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def txt(r,p): return (r/p).read_text()
B,C=H(b),H(c); assert len(B)==len(C)==1823
expected=set((pkg/'26719_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()); assert expected=={
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/version.properties'}
assert {k for k in B|C if B.get(k)!=C.get(k)}==expected
v=txt(c,'app/version.properties'); assert 'VERSION_NAME=0.9726719' in v and 'VERSION_BUILD=26719' in v
# Every 26718 high-zoom integration owner other than the shader object stays byte-identical to successful R1.
for rel in [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/RawStackContracts.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl']:
    assert (b/rel).read_bytes()==(c/rel).read_bytes(),rel
bridge=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt')
for t in ['!sabreSuperResEnabled && displayedGlobalZoom >= 20f','IRIS_26718_HIGH_ZOOM_ACTIVATION','enableHighZoomDetail = highZoomDetailEnabled','detailOwner=${if (highZoomDetailEnabled) "NORMAL_SCALAR_2X_LUMA_ROI" else "NONE"}']:
    assert t in bridge,t
stack=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
for t in ['if (enableHighZoomDetail) {','runHighZoomDetailGpu26718(','enableHighZoomDetail && frame.role == RawBurstFrameRole.NORMAL','allAdmittedNormal=true','shortDetailEvidence=false','longDetailEvidence=false']:
    assert t in stack,t
# New permanent regression: high-zoom shader derivation must be lazy, so disabled <20x ordinary Sabre object init cannot execute it.
sh=txt(c,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt')
assert 'IRIS_26719_HIGH_ZOOM_LAZY_ISOLATION' in sh
assert 'val highZoomDetailMerge26718: String by lazy {' in sh
assert 'val highZoomDetailResolve26718: String by lazy {' in sh
assert 'val highZoomDetailMerge26718: String = true2xMerge26564' not in sh
assert '26719 high-zoom shader anchor missing:' in sh and '26719 high-zoom shader anchor duplicated:' in sh
# Reproduce the exact post-trimIndent transformation that failed in 26718 R1.
def triple(name):
    m=re.search(r'val\s+'+re.escape(name)+r'\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',sh,re.S); assert m,name
    return textwrap.dedent(m.group(1))+'\n'
merge=triple('true2xMerge26564')
out='layout(location = 0) out vec4 oColorAndRWeight;\nlayout(location = 1) out vec2 oWeightsGb;\nlayout(location = 2) out vec4 oPhaseOccupancy;\nlayout(location = 3) out vec4 oTemporalLumaStats;'
rgb='    color *= frameWeight;\n    weights *= frameWeight;\n    oColorAndRWeight = vec4(color, weights.r);\n    oWeightsGb = weights.gb;\n\n'
assert merge.count(out)==1,('post-trim outputs anchor count',merge.count(out))
assert merge.count(rgb)==1,('post-trim rgb-write anchor count',merge.count(rgb))
merged=merge.replace(out,'layout(location = 0) out vec4 oTemporalLumaStats;\nlayout(location = 1) out vec4 oPhaseOccupancy;',1).replace(rgb,'',1)
assert 'oColorAndRWeight' not in merged and 'oWeightsGb' not in merged
# Program creation must remain inside the gated high-zoom execution function only.
use='GlesMgcRawSabreShaders.highZoomDetailMerge26718'
assert stack.count(use)==1
pos=stack.index(use); fn=stack.rfind('private fun runHighZoomDetailGpu26718',0,pos); assert fn>=0
assert stack.index('require(enableHighZoomDetail && !enableSabreSuperRes)')>pos
print('PASS 26719 regressions: successful-R1 high-zoom architecture unchanged; <20 activation remains false; new shader derivation is lazy; exact post-trim anchors proven; high-zoom programs remain gated')
