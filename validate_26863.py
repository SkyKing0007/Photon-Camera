#!/usr/bin/env python3
"""26863: exact 26862 Actions candidate and B-owned source-only changed allowlist."""
from pathlib import Path
import hashlib,subprocess,sys
B,C=map(Path,sys.argv[1:3]);R=Path(__file__).resolve().parent
assert B.is_dir() and C.is_dir()
def U(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def M(name):
    ls=(R/name).read_text().splitlines();assert ls,name
    out={p:h for h,p in (l.split('  ',1) for l in ls)}
    assert len(out)==len(ls),(name,'duplicates')
    return out
b,c=U(B),U(C)
assert len(b)==1840 and len(c)==1841
assert b==M('26863_BASE_26862_FULL_APP.sha256'), 'base != exact successful 26862 Actions source'
assert c==M('26863_EXPECTED_CANDIDATE_FULL_APP.sha256'), 'candidate not frozen / mismatched'
changed=set((R/'26863_ALL_CANDIDATE_CHANGED_PATHS.txt').read_text().splitlines())
source=set((R/'26863_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
assert len(source)==5 and changed==source|{'app/version.properties'} and len(changed)==6
assert set(b)^set(c)=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26863BNoiseContinuity.kt'}
actual={p for p in set(b)|set(c) if b.get(p)!=c.get(p)}
assert actual==changed,(actual^changed)
assert M('26863_REPLACEMENT_FILES_SHA256.sha256')=={p:c[p] for p in changed}
assert M('26863_PRIOR_SOURCE_HASHES.sha256')=={p:b[p] for p in changed if p in b}
protected=M('26863_PROTECTED_26862.sha256')
assert len(protected)==1835 and protected=={p:h for p,h in b.items() if p not in changed}
assert all(c[p]==h for p,h in protected.items())
for name in ('26863_NATIVE_PROTECTED_26862.sha256','26863_DNG_WRITER_26862.sha256','26863_VENDOR_PROTECTED_26862.sha256','26863_SHADER_ASSETS_PROTECTED_26862.sha256'):
    m=M(name); assert m and all(p in protected and c[p]==h for p,h in m.items()),name
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726863','VERSION_BUILD=26863']
for name in ('GlesIris26860BBurstNoise.kt','GlesIris26858BNoiseHighlight.kt','GlesIris26856RawrColorContract.kt'):
    p='app/src/main/java/com/hinnka/mycamera/processor/'+name
    assert b[p]==c[p],('protected B owner was altered',name)
P=C/'app/src/main/java/com/hinnka/mycamera/processor'
s=(P/'GlesMgcRawSpatialStacker.kt').read_text()
assert 'check(burst.measuredPhases == 4)' in s and 'camera2Fallback=false' in s
assert 'renderIris26863BPostLscChroma(' in s and 'bNoiseVariance26863 = measuredNoise26863' in s
assert 'bNoiseSupport26863 = measuredSupport' in s and 'bNoiseSupport26863 = support' in s
assert s.count('bBurstNoise26860,')>=4
assert 'bCamera2ProfileForFrame26861' not in s and 'CAMERA2_FALLBACK_' not in s
assert 'renderIris26858BNoiseClean(' not in s and 'renderIris26858BResidualChroma(' not in s
assert 'if (!iris26856BOnlyIndependentPublication &&' in s
assert s.index('bLensCorrected26859 = renderIris26859BLensShading(') < s.index('bNoiseCorrected26863 = renderIris26863BPostLscChroma(') < s.index('bRecovered26858 = renderIris26858BHighlightColor(') < s.index('defringed = renderRawrLabDefringe26856(') < s.index('fcc = renderRawrFalseColor26856(')
assert 'renderSabreNormalDngMerge(' in s and 'normalDngAccumulator != 0' in s
sh=(P/'GlesMgcRawSabreShaders.kt').read_text()
assert 'uBNoiseMomentOwner26858!=0 ? w2 : 0.0' in sh and '256.0*w2' in sh
assert 'vec4(w2,quadMean26853*quadMean26853*validWeight,0.0,0.0)' in sh
assert 'GLES30.GL_RGBA16F else GLES30.GL_RG16F' in s
assert 'oBNoiseVariance26863=noiseCanonical' in (P/'GlesIris26856AmazeCfaHandoff.kt').read_text()
assert 'oBNoiseVariance26863=valid>0.5?vCanonical:vec4(0.0)' in (P/'GlesIris26856True2xCfa.kt').read_text()
assert 'weightSquared/(weight*weight)' in (P/'GlesIris26856True2xCfa.kt').read_text()
n=(P/'GlesIris26863BNoiseContinuity.kt').read_text()
assert 'uUsePhysicalLsc == 0' in n and '*gain*gain' in n and 'rgbDelta-=vec3(luma(rgbDelta))' in n
# Exact historical 26862 regression against its own successful source, not the
# 26863 transformed candidate alone; avoids erasing an old failure condition.
old=R/'TESTS/test_26862_b_raw_only_noise_contract.py';assert old.is_file()
t=subprocess.run([sys.executable,'-B',str(old),str(B/'app')],capture_output=True,text=True)
assert t.returncode==0,('historical 26862',t.stdout,t.stderr)
new=R/'TESTS/test_26863_b_noise_continuity.py';assert new.is_file()
t=subprocess.run([sys.executable,'-B',str(new),str(C/'app')],capture_output=True,text=True)
assert t.returncode==0,('candidate 26863 regression',t.stdout,t.stderr)
print('PASS 26863 exact 1840->1841 compiled universe; strict 5 B runtime + 1 version; 1835 byte-protected; prior 26862 real regressions preserved')
