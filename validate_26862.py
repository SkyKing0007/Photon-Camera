#!/usr/bin/env python3
"""26862: exact 26861 compiled authority, protected universe and B-only regressions."""
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
assert len(b)==len(c)==1840 and b.keys()==c.keys(),(len(b),len(c))
assert b==manifest('26862_BASE_26861_FULL_APP.sha256'),'actual 26861 Actions compiled candidate mismatch'
assert c==manifest('26862_EXPECTED_CANDIDATE_FULL_APP.sha256'),'frozen 26862 candidate mismatch'
source=set((R/'26862_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
allpaths=set((R/'26862_ALL_CANDIDATE_CHANGED_PATHS.txt').read_text().splitlines())
assert len(source)==2 and allpaths==source|{'app/version.properties'} and len(allpaths)==3
assert source=={'app/src/main/java/com/hinnka/mycamera/processor/'+n for n in (
 'GlesIris26860BBurstNoise.kt','GlesMgcRawSpatialStacker.kt')}
mod={p for p in c if b[p]!=c[p]}
assert mod==allpaths,(mod^allpaths)
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726862','VERSION_BUILD=26862']
protected=manifest('26862_PROTECTED_26861.sha256');assert len(protected)==1837
assert protected=={p:h for p,h in b.items() if p not in allpaths}
assert all(c[p]==h for p,h in protected.items())
for name in ('26862_NATIVE_PROTECTED_26861.sha256','26862_DNG_WRITER_26861.sha256','26862_VENDOR_PROTECTED_26861.sha256','26862_SHADER_ASSETS_PROTECTED_26861.sha256'):
 m=manifest(name);assert len(m)>0 and all(p in protected and c[p]==h for p,h in m.items()),name
assert manifest('26862_REPLACEMENT_FILES_SHA256.sha256')=={p:c[p] for p in allpaths}
assert manifest('26862_PRIOR_SOURCE_HASHES.sha256')=={p:b[p] for p in allpaths}
PR='app/src/main/java/com/hinnka/mycamera/processor/'
# 26861 color/highlight, DNG/long, A, vendor, GLSL owners are all byte-exact.
for path in ('GlesIris26858BNoiseHighlight.kt','GlesMgcRawSabreShaders.kt'):
 assert (B/PR/path).read_bytes()==(C/PR/path).read_bytes()
S=(C/PR/'GlesMgcRawSpatialStacker.kt').read_text()
assert 'GlesIris26860BBurstNoise.estimate(' in S and 'bEmpiricalNoise26861 = bBurstNoise26860' in S
assert 'if (!iris26856BOnlyIndependentPublication &&' in S
assert 'bCamera2ProfileForFrame26861' not in S and 'CAMERA2_FALLBACK_' not in S
assert 'normalDngAccumulator != 0' in S and 'renderSabreNormalDngMerge(' in S
assert 'bRecovered26858 = renderIris26858BHighlightColor(' in S
assert S.index('bRecovered26858 = renderIris26858BHighlightColor(') < S.index('defringed = renderRawrLabDefringe26856(') < S.index('fcc = renderRawrFalseColor26856(')
# Historical failures stay permanent and run against the source they originally targeted.
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

old=R/'TESTS/test_26861_b_burst_only_noise_contract.py'
assert old.is_file()
run=subprocess.run([sys.executable,'-B',str(old),str(B/'app')],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
assert run.returncode==0,f'26861 historical regression against actual 26861 candidate failed: {run.stdout}'
print('PASS historical 26861 regression against exact compiled 26861 source')
new=R/'TESTS/test_26862_b_raw_only_noise_contract.py'
assert new.is_file()
run=subprocess.run([sys.executable,'-B',str(new),str(C/'app')],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
assert run.returncode==0,f'26862 consumer/capture-isolation regression: {run.stdout}'
print(run.stdout.strip())
print('PASS 26862 exact 1840-file prior/candidate, 1837 byte-protected; two B Kotlin+version; A/LONG/DNG/UHDR/native/vendor unchanged')
