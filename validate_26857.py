#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,sys
B,C=map(Path,sys.argv[1:3]);R=Path(__file__).resolve().parent
assert B.is_dir() and C.is_dir()
def U(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def manifest(name):
 ls=(R/name).read_text().splitlines();assert ls
 a=dict((p,d) for d,p in (l.split('  ',1) for l in ls));assert len(a)==len(ls),(name,len(a),len(ls));return a
b,a=U(B),U(C)
assert len(b)==len(a)==1838,(len(b),len(a))
assert b==manifest('26857_BASE_26856_FULL_APP.sha256'),'26856 compiled authority mismatch'
assert a==manifest('26857_EXPECTED_CANDIDATE_FULL_APP.sha256'),'26857 frozen candidate mismatch'
source=set((R/'26857_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
allpaths=set((R/'26857_ALL_CANDIDATE_CHANGED_PATHS.txt').read_text().splitlines())
assert len(source)==5 and allpaths==source|{'app/version.properties'} and len(allpaths)==6
assert all(p.startswith('app/src/main/java/') for p in source),source
add=set(a)-set(b);delete=set(b)-set(a);mod={p for p in a.keys()&b.keys() if a[p]!=b[p]}
assert not add and not delete and mod==allpaths,(add,delete,mod^allpaths)
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726857','VERSION_BUILD=26857']
protect=manifest('26857_PROTECTED_26856.sha256');assert len(protect)==1832
assert protect=={p:h for p,h in b.items() if p not in allpaths}
assert all(a[p]==h for p,h in protect.items())
for name in ('26857_NATIVE_PROTECTED_26856.sha256','26857_DNG_WRITER_26856.sha256','26857_VENDOR_PROTECTED_26856.sha256','26857_SHADER_ASSETS_PROTECTED_26856.sha256'):
 m=manifest(name);assert len(m)>0 and all(p in protect and protect[p]==h and a[p]==h for p,h in m.items()),name
assert manifest('26857_REPLACEMENT_FILES_SHA256.sha256')=={p:a[p] for p in allpaths}
# Reapply permanent existing 26856 failure regressions to intact historical input.
tests=sorted((R/'TESTS').glob('test_26856*.py'))
assert len(tests)==13,(len(tests),'permanent inherited regressions missing')
for test in tests:
 run=subprocess.run([sys.executable,'-B',str(test)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if run.returncode:raise AssertionError(f'{test.name} failed:\n{run.stdout[-4500:]}')
 print('PASS inherited regression',test.name)
new=R/'TESTS/test_26857_b_color_chroma_perlens_names.py';assert new.is_file()
run=subprocess.run([sys.executable,'-B',str(new)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
assert run.returncode==0,f'26857 actual failure regression FAILED: {run.stdout[-4500:]}'
print('PASS 26857 regression',new.name)
print('PASS 26857 strict complete 1838-file authority-seeded 6-change allowlist; 1832 original protected; native/DNG/vendor/shader invariance; 14 regressions')
