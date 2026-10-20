#!/usr/bin/env python3
"""26861 exact authority-seeded scope/invariance + permanent regression gates.

Every inherited applicable regression is replayed in the order 26856..26861;
26860's historic fidelity test checks unchanged 26860 payload as originally
published, and the 26861 test supersedes its B spatial-denoiser assertions.
"""
from pathlib import Path
import hashlib,subprocess,sys,re
B,C=map(Path,sys.argv[1:3]);R=Path(__file__).resolve().parent
assert B.is_dir() and C.is_dir()
def U(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def manifest(name):
 ls=(R/name).read_text().splitlines();assert ls,name
 m={p:h for h,p in (l.split('  ',1) for l in ls)}
 assert len(m)==len(ls),(name,'duplicate entry')
 return m
b,c=U(B),U(C)
assert len(b)==1840 and len(c)==1840,(len(b),len(c))
assert b==manifest('26861_BASE_26860_FULL_APP.sha256'), 'compiled 26860 authority mismatch'
assert c==manifest('26861_EXPECTED_CANDIDATE_FULL_APP.sha256'), 'frozen 26861 candidate mismatch'
source=set((R/'26861_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
allpaths=set((R/'26861_ALL_CANDIDATE_CHANGED_PATHS.txt').read_text().splitlines())
assert len(source)==3 and allpaths==source|{'app/version.properties'} and len(allpaths)==4
assert source=={'app/src/main/java/com/hinnka/mycamera/processor/'+n for n in (
 'GlesIris26858BNoiseHighlight.kt','GlesIris26860BBurstNoise.kt','GlesMgcRawSpatialStacker.kt')}
add=set(c)-set(b);deleted=set(b)-set(c);mod={p for p in c.keys()&b.keys() if b[p]!=c[p]}
assert not add and not deleted and mod==allpaths,(add,deleted,mod^allpaths)
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726861','VERSION_BUILD=26861']
protected=manifest('26861_PROTECTED_26860.sha256');assert len(protected)==1836
assert protected=={p:h for p,h in b.items() if p not in allpaths}
assert all(c[p]==h for p,h in protected.items())
for name in ('26861_NATIVE_PROTECTED_26860.sha256','26861_DNG_WRITER_26860.sha256','26861_VENDOR_PROTECTED_26860.sha256','26861_SHADER_ASSETS_PROTECTED_26860.sha256'):
 m=manifest(name);assert len(m)>0 and all(p in protected and c[p]==h for p,h in m.items()),name
assert manifest('26861_REPLACEMENT_FILES_SHA256.sha256')=={p:c[p] for p in allpaths}
assert manifest('26861_PRIOR_SOURCE_HASHES.sha256')=={p:b[p] for p in allpaths}
PR='app/src/main/java/com/hinnka/mycamera/processor/'
fb=(B/PR/'GlesIris26858BNoiseHighlight.kt').read_text()
fc=(C/PR/'GlesIris26858BNoiseHighlight.kt').read_text()
for n in ('bClipAccumulate','bClipNormalize','bHighlightRecover','bLensShade'):
 reg=r'val\s+'+n+r'\s*=\s*"""(.*?)""".trimIndent\(\)'
 l=re.findall(reg,fb,re.S);r=re.findall(reg,fc,re.S)
 assert len(l)==len(r)==1 and l==r,('protected 26859 B source fragment',n)
S=(C/PR/'GlesMgcRawSpatialStacker.kt').read_text()
assert 'GlesIris26860BBurstNoise.estimate(' in S and 'bEmpiricalNoise26861 = bBurstNoise26860' in S
assert 'normalDngAccumulator != 0' in S and 'renderSabreNormalDngMerge(' in S
assert 'bMotionOnlyWeight26861' in fc and 'bWeightedCfaIdentity26861' in fc
assert 'if (burst.mode == "BURST_ALL_PHASE_SHOT_READ") burst else' in S
assert 'IRIS_26861_NO_VALID_NOISE_PROFILE' in S
assert 'bFrameNoise26861' in S and 'bCamera2ProfileForFrame26861(' in S
assert 'physicalRead[c]=profile.read[phase].coerceAtLeast(1.0e-10f)' not in S
assert 'bCfaNoise' not in fc and 'bResidualChroma' not in fc
# Historical protection is a complete byte manifest: A, DNG, LONG, vendor and native MUST match.
# Existing prior tests operate on original, unchanged prior handoff payloads in repo root.
tests=sorted((R/'TESTS').glob('test_26856*.py'))
assert len(tests)==13,('26856 permanent regressions missing',len(tests))
assert (R/'TESTS/test_26857_b_color_chroma_perlens_names.py').is_file()
for testspec in (
 tests+[R/'TESTS/test_26857_b_color_chroma_perlens_names.py']+
 sorted((R/'TESTS').glob('test_26858*.py'))+
 sorted((R/'TESTS').glob('test_26859*.py'))+
 sorted((R/'TESTS').glob('test_26860*.py'))
):
 run=subprocess.run([sys.executable,'-B',str(testspec)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 assert run.returncode==0,f'inherited regression {testspec.name} failed: {run.stdout[-4000:]}'
 print('PASS inherited permanent regression',testspec.name)
new=R/'TESTS/test_26861_b_burst_only_noise_contract.py'
assert new.is_file()
run=subprocess.run([sys.executable,'-B',str(new),str(C/'app')],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
assert run.returncode==0,f'26861 positive consumer regression: {run.stdout}'
print(run.stdout.strip())
print('PASS 26861 exact 1840 compiled-candidate authority/1840 frozen candidate, 1836 protected; 3 B Kotlin + version; native/vendor/DNG/LSC/highlight/A invariants')
