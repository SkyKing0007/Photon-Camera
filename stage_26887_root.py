#!/usr/bin/env python3
"""26887 fail-closed three-stage root scope/integrity check.

`--draft-scope` checks the currently available stage-root bytes without
claiming a deliverable. Default mode additionally REQUIRES all final release
runner/generator/contract inputs and their sealed hash manifests.
"""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def man(name):
 out={}
 for line in (R/name).read_text().splitlines():
  h,k=line.split('  ',1)
  assert len(h)==64 and k not in out and '/' not in h and all(x in '0123456789abcdef' for x in h),(name,line)
  out[k]=h
 return out
old=man('26887_BASE_26886_FULL_APP.sha256')
new=man('26887_EXPECTED_CANDIDATE_FULL_APP.sha256')
protected=man('26887_UNCHANGED_PROTECTED.sha256')
allow=(R/'26887_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2010 and len(new)==2020 and len(protected)==2003 and len(allow)==17
assert allow==sorted(set(allow))
existing={k for k in old if k in new and old[k]!=new[k]}
added=set(new)-set(old)
assert len(existing)==7 and len(added)==10 and set(old)-set(new)==set()
assert set(allow)==existing|added
assert existing&{'app/version.properties'}=={'app/version.properties'}
assert all(k.startswith('app/src/main/cpp/iris26864/') for k in set(allow)-{'app/version.properties'})
assert set(protected)==set(old)-existing
assert all(old[k]==new[k]==h for k,h in protected.items())
assert (R/'26887_DELETIONS.txt').read_bytes()==b''
payload=R/'handoff_payload_26887'
actual={'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}
assert actual==set(allow)
assert all(sha(payload/k)==new[k] for k in allow)
assert man('26887_PAYLOAD_SHA256.txt')=={'handoff_payload_26887/'+k:new[k] for k in allow}
assert (R/'TRIGGER_26887.txt').read_bytes()==b'RUN_26887_B_OFF_RAW_WITNESS_HDRQ_MOTION_V1\n'
w=(R/'.github/workflows/build-26887-iris-rawr.yml').read_bytes()
prev=(R/'.github/workflows/build-26886-iris-rawr.yml').read_bytes()
assert hashlib.sha256(prev).hexdigest()=='6935d2cf2c87bcb601dcc3492cdafe29d2edb0c3e6d92cecb02b2f0e668270a4', 'EXACT SUCCESSFUL 26886 workflow byte drift'
start=b'          test -f TRIGGER_26882.txt'
end=b'          test "$(find handoff_payload_26886 -type f | wc -l)" -eq 2\n          ! find . -type f -name \'*.apk\' | grep -q .'
assert w.count(start)==prev.count(start)==w.count(end)==prev.count(end)==1
assert w.split(start,1)[1].split(end,1)[0]==prev.split(start,1)[1].split(end,1)[0], 'historical Actions block drift'
assert w.count(b"      - 'TRIGGER_26887.txt'")==1
assert b"      - 'TRIGGER_26886.txt'" not in w
assert w.count(b'          bash build_26887_iris_rawr.sh')==1
assert w.count(b'          python3 -S generate_26887_build.py .')==2
assert w.count(b'          python3 -S stage_26887_root.py')==1
assert w.count(b'          sha256sum -c 26887_HANDOFF_HASHES.sha256')==1
assert w.count(b'          test "$(find handoff_payload_26887 -type f | wc -l)" -eq 17')==1
assert b'3f816088f564bfd575d5dc8e1681b9b1b18ec435de41ed34f2c22df866c5e8fa' in w
assert b'IrisCamera-0.9726887-26887-iris-rawr-debug.apk' in w
assert '26887' in (R/'26887_RUNTIME_PROVENANCE.json').read_text()
assert not any(p.suffix.lower()=='.apk' for p in R.rglob('*') if p.is_file())
print('PASS 26887 draft scope: 2010->2020, 7 changed, 10 additions, 2003 protected, 17 payload paths; historical V6 workflow block unchanged')
# Draft scope is NOT a release pass. Default mode blocks release on missing
# executable runner generation and the final sealed upload hash contract.
if '--draft-scope' in sys.argv[1:]:
 assert sys.argv[1:]==['--draft-scope']
 print('NOT RUN 26887 final generator/17-stage/clean-extracted handoff: DRAFT ONLY')
 sys.exit(0)
assert len(sys.argv)==1
for name in ('generate_26887_build.py','regressions/26887_successor_contract.py',
             '26887_REPOSITORY_UPLOAD_ALLOWLIST.txt','26887_HANDOFF_HASHES.sha256'):
 assert (R/name).is_file(),('release artifact missing',name)
package=man('26887_HANDOFF_HASHES.sha256')
assert all((R/k).is_file() and sha(R/k)==v for k,v in package.items()),'sealed staged bytes tampered'
upload=(R/'26887_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert upload==sorted(set(upload))
assert len(upload)==37,('unexpected upload additions',len(upload))
assert set(upload)==set(package)|{'26887_HANDOFF_HASHES.sha256','26887_REPOSITORY_UPLOAD_ALLOWLIST.txt'}
assert 'build_26887_iris_rawr.sh' not in upload
assert all('__pycache__' not in k and not k.endswith('.pyc') for k in upload)
print('PASS sealed 26887 root; NOTE: this alone does not prove 17-stage runner or real compilers')
