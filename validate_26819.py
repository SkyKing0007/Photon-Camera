#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys,re
B,C=map(Path,sys.argv[1:3])
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
POST='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
A={S,'app/version.properties'}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(r): return {p.relative_to(r).as_posix():h(p) for p in (r/'app').rglob('*') if p.is_file()}
b,c=U(B),U(C); changed={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert changed==A,(changed,A); assert len(b)==1783 and len(c)==1783
v=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726819' in v and 'VERSION_BUILD=26819' in v
s=(C/S).read_text(); bs=(B/S).read_text()
assert s.count('IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER')==1
# NORMAL copy only: validity-aware green prediction + color-site validity + neutral missing-evidence fallback.
normal=s[:s.index('        void sameLocationChroma26793(', s.index('IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER'))]
assert normal.count('IRIS_26819_NORMAL_CLIPPED_CHROMA_VALIDITY_OWNER')==1
assert s.count('float siteValid = clamp(greenSupport[sx][sy], 0.0, 1.0);')==1
assert s.count('float differenceWeight = colorWeight * greenConfidence * siteValid;')==1
assert s.count('? redDifferenceSum / redDifferenceWeight : 0.0;')==1
assert s.count('? blueDifferenceSum / blueDifferenceWeight : 0.0;')==1
assert s.count('dR = measuredDR * redPhysicalFraction;')==1
assert s.count('dB = measuredDB * bluePhysicalFraction;')==1
assert s.count('calculationCfa26793, weights, sourceValidity, type, covariance, 1,')==1
# The old defective NORMAL call and clipped legacy chroma fallback must be gone from the NORMAL shader.
merge_start=s.index('val merge = """')
merge_end=s.index('""".trimIndent()',merge_start)
merge=s[merge_start:merge_end]
assert 'calculationCfa26793, weights, sourceValidity, type, covariance, 0,' not in merge
assert 'float legacyDR = legacyRgb.r - legacyRgb.g;' not in merge
assert 'float legacyDB = legacyRgb.b - legacyRgb.g;' not in merge
# SHORT shader must remain byte-identical to successful 26818 authority.
name='val universalNormalMasterShortFusion26651 = """'
ci=s.index(name); bi=bs.index(name)
ce=s.index('""".trimIndent()',ci); be=bs.index('""".trimIndent()',bi)
assert s[ci:ce]==bs[bi:be]
# 26818 green cleanup and all protected downstream owners remain frozen.
assert h(B/POST)==h(C/POST)
for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/res/xml/preferences.xml','app/src/main/java/com/particlesdevs/photoncamera/util/Log.java','app/src/main/java/com/particlesdevs/photoncamera/util/MotionTrace.java']:
    assert h(B/rel)==h(C/rel),rel
post=(C/POST).read_text()
for token in ['IRIS_26818_STRICTER_INDEPENDENT_CHROMA_MAGNITUDE_PROOF','IRIS_26818_SELECTIVE_GREEN_RESIDUAL_DENOISE','IRIS_26818_VGN_GREEN_RESIDUAL_CLEANUP','smoothstep(0.70, 0.90','smoothstep(0.030, 0.080','greenCleanupAuthority = 0.75']:
    assert token in post,token
print('PASS 26819 exact 2-path NORMAL-Sabre/version scope; SHORT/VGN/Resolve/downstream owners protected')
