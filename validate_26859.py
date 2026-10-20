#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
B,C=map(Path,sys.argv[1:3]);R=Path(__file__).resolve().parent
assert B.is_dir() and C.is_dir()
def U(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def manifest(name):
 ls=(R/name).read_text().splitlines();assert ls
 m=dict((p,h) for h,p in (l.split('  ',1) for l in ls));assert len(m)==len(ls),(name,len(m),len(ls));return m
b,c=U(B),U(C)
assert len(b)==1839 and len(c)==1839,(len(b),len(c))
assert b==manifest('26859_BASE_26858_FULL_APP.sha256'),'26858 compiled authority mismatch'
assert c==manifest('26859_EXPECTED_CANDIDATE_FULL_APP.sha256'),'26859 frozen candidate mismatch'
source=set((R/'26859_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
allpaths=set((R/'26859_ALL_CANDIDATE_CHANGED_PATHS.txt').read_text().splitlines())
assert len(source)==2 and allpaths==source|{'app/version.properties'} and len(allpaths)==3
assert all(p.startswith('app/src/main/java/') for p in source)
add=set(c)-set(b);delete=set(b)-set(c);mod={p for p in c.keys()&b.keys() if b[p]!=c[p]}
assert not add and not delete and mod==allpaths,(add,delete,mod^allpaths)
assert source=={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26858BNoiseHighlight.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'}
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726859','VERSION_BUILD=26859']
protected=manifest('26859_PROTECTED_26858.sha256');assert len(protected)==1836
assert protected=={p:h for p,h in b.items() if p not in allpaths}
assert all(c[p]==h for p,h in protected.items())
for name in ('26859_NATIVE_PROTECTED_26858.sha256','26859_DNG_WRITER_26858.sha256','26859_VENDOR_PROTECTED_26858.sha256','26859_SHADER_ASSETS_PROTECTED_26858.sha256'):
 m=manifest(name);assert len(m)>0 and all(p in protected and c[p]==h for p,h in m.items()),name
assert manifest('26859_REPLACEMENT_FILES_SHA256.sha256')=={p:c[p] for p in allpaths}
assert manifest('26859_PRIOR_SOURCE_HASHES.sha256')=={p:b[p] for p in allpaths if p in b}
# Inherited exact regressions, including 26857 WB and lens preservation.
tests=sorted((R/'TESTS').glob('test_26856*.py'))
assert len(tests)==13,(len(tests),'permanent 26856 tests missing')
assert (R/'TESTS/test_26857_b_color_chroma_perlens_names.py').is_file(), '26857 WB / per-lens permanent regression absent'
for test in sorted((R/'TESTS').glob('test_26856*.py')) + [R/'TESTS/test_26857_b_color_chroma_perlens_names.py'] + sorted((R/'TESTS').glob('test_26858*.py')) + sorted((R/'TESTS').glob('test_26859*.py')):
 run=subprocess.run([sys.executable,'-B',str(test)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 assert run.returncode==0,f'{test.name} failed: {run.stdout[-4000:]}'
 print('PASS 26859 inherited or new permanent regression',test.name)
print('PASS 26859 exact compiled authority 1839 and candidate 1839; 2 B runtime paths plus one version; 1836 protected; native/vendor/DNG/shaders byte-exact')
