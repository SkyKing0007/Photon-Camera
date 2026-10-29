#!/usr/bin/env python3
"""26887 successor exact successful 26886 2010-file compiled runtime authority."""
from pathlib import Path
import argparse,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--root',type=Path);p.add_argument('--transform',action='store_true');a=p.parse_args()
R=(a.root or Path(__file__).parent).resolve();B=a.base.resolve();C=a.candidate.resolve()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def man(name):
 out={}
 for s in (R/name).read_text().splitlines():
  h,k=s.split('  ',1);assert k not in out and len(h)==64;out[k]=h
 return out
old=man('26887_BASE_26886_FULL_APP.sha256');new=man('26887_EXPECTED_CANDIDATE_FULL_APP.sha256');protected=man('26887_UNCHANGED_PROTECTED.sha256')
allow=(R/'26887_CHANGED_ALLOWLIST.txt').read_text().splitlines()
existing={k for k in old if old.get(k)!=new.get(k)};added=set(new)-set(old)
assert len(old)==2010 and len(new)==2020 and len(protected)==2003
assert len(existing)==7 and len(added)==10 and set(old)-set(new)==set()
assert 'app/version.properties' in existing and all(k.startswith('app/src/main/cpp/iris26864/') for k in (existing|added)-{'app/version.properties'})
assert allow==sorted(existing|added) and not (R/'26887_DELETIONS.txt').read_bytes()
# Staged hashes are checked from the Actions/repository ROOT, never from
# inside handoff_payload_26887. This is the proven V6 CLI/path contract.
payload_sha=man('26887_PAYLOAD_SHA256.txt')
assert set(payload_sha)=={'handoff_payload_26887/'+k for k in allow},'staged payload path/root mismatch'
assert all(payload_sha['handoff_payload_26887/'+k]==new[k] for k in allow)
assert all((R/'handoff_payload_26887'/k).is_file() and
           sha(R/'handoff_payload_26887'/k)==new[k] for k in allow), 'staged runtime source drift'
assert set(protected)==set(old)-existing and all(old[k]==new[k]==h for k,h in protected.items())
assert B!=C and not B.is_relative_to(C) and not C.is_relative_to(B)
def universe(root):
 return {'app/'+f.relative_to(root/'app').as_posix() for f in (root/'app').rglob('*') if f.is_file() and f.relative_to(root/'app').parts[0] not in ('build','.cxx')}
assert universe(B)==set(old)
assert all((B/k).is_file() and sha(B/k)==h for k,h in old.items()),'successful 26886 authority drift'
if a.transform:
 payload=R/'handoff_payload_26887'
 actual={'app/'+f.relative_to(payload/'app').as_posix() for f in (payload/'app').rglob('*') if f.is_file()}
 assert actual==set(allow)
 if C.exists():shutil.rmtree(C)
 shutil.copytree(B,C)
 for k in allow:
  assert sha(payload/k)==new[k]
  (C/k).parent.mkdir(parents=True,exist_ok=True)
  (C/k).write_bytes((payload/k).read_bytes())
assert universe(C)==set(new),('candidate universe drift',sorted(universe(C)^set(new))[:10])
assert all((C/k).is_file() and sha(C/k)==h for k,h in new.items()),'frozen 26887 candidate drift'
assert (C/'app/version.properties').read_text().splitlines()[-2:]==['VERSION_NAME=0.9726887','VERSION_BUILD=26887']
print('PASS 26887 candidate-first 2010->2020 exact compiled source: 7 changed existing (version included), 10 additions, 2003 protected')
