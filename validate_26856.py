#!/usr/bin/env python3
# Version-scoped extension: preserve exact 26855 authority-seeded universe checks.
from pathlib import Path
import hashlib,subprocess,sys
B,C=map(Path,sys.argv[1:3]); R=Path(__file__).resolve().parent
assert B.is_dir() and C.is_dir()
def U(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
def manifest(name):
 lines=(R/name).read_text().splitlines(); assert lines
 a=dict((p,d) for d,p in (line.split('  ',1) for line in lines));assert len(lines)==len(a),(name,len(lines),len(a));return a
before,after=U(B),U(C)
assert len(before)==1786 and len(after)==1838,(len(before),len(after))
assert before==manifest('26856_BASE_26855_FULL_APP.sha256'),'compiled authority differs'
assert after==manifest('26856_EXPECTED_CANDIDATE_FULL_APP.sha256'),'candidate differs from frozen compiler input'
source=set((R/'26856_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
allpaths=set((R/'26856_ALL_CANDIDATE_CHANGED_PATHS.txt').read_text().splitlines())
assert len(source)==66 and allpaths==source|{'app/version.properties'} and len(allpaths)==67
assert all(s.startswith('app/src/') and not s.startswith(('app/build/','app/.cxx/')) for s in source)
added=set(after)-set(before);deleted=set(before)-set(after)
modified={p for p in before.keys() & after.keys() if before[p]!=after[p]}
assert len(added)==52 and len(modified)==15 and not deleted,(len(added),len(modified),deleted)
assert added|modified==allpaths,'STRICT source + version allowlist equality violated'
assert before['app/version.properties']!=after['app/version.properties']
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726856','VERSION_BUILD=26856']
protected=manifest('26856_PROTECTED_26855.sha256');assert len(protected)==1771
assert protected=={k:v for k,v in before.items() if k not in allpaths}
assert all(after[k]==v for k,v in protected.items())
# Explicit complete source-domain cardinality and protected native/DNG/vendor/shader bytes.
for name,count in [('26856_NATIVE_PROTECTED_26855.sha256',818),('26856_DNG_WRITER_26855.sha256',3),('26856_VENDOR_PROTECTED_26855.sha256',113),('26856_SHADER_ASSETS_PROTECTED_26855.sha256',275)]:
 m=manifest(name);assert len(m)==count,(name,len(m));assert all(protected[p]==d and after[p]==d for p,d in m.items()),name
assert {p for p in after if p.startswith('app/src/') and p not in before}==added
assert all(p in after and after[p]==v for p,v in manifest('26856_REPLACEMENT_FILES_SHA256.sha256').items())
# Replay all 12 applicable source-contract regressions on the ACTUAL packaged payload.
for test in sorted((R/'TESTS').glob('test_26856*.py')):
 r=subprocess.run([sys.executable,'-B',str(test)],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if r.returncode:raise SystemExit(f'FAIL {test.name} exit={r.returncode}\n{r.stdout[-3000:]}')
 print('PASS 26856 permanent regression:',test.name)
assert len(list((R/'TESTS').glob('test_26856*.py')))==12
print('PASS 26856 strict source 66 + version 1, 1786/1838 complete file universe, 1771 protected, native/DNG/vendor/shader invariance, 12 regressions')
