#!/usr/bin/env python3
"""26949 B OFF-only source allowlist and actual published 26948 identity proof."""
import pathlib,hashlib,sys
R=pathlib.Path(__file__).resolve().parent
C={'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
def read(n):
 out={}
 for l in (R/n).read_text().splitlines():
  h,p=l.split('  ',1)
  assert len(h)==64 and p not in out and p.startswith('app/')
  out[p]=h
 return out
def main():
 a=read('26949_BASE_26948_FULL_APP.sha256');b=read('26949_EXPECTED_FULL_APP.sha256');p=read('26949_PROTECTED_SOURCE.sha256')
 assert len(a)==len(b)==2054 and a.keys()==b.keys()
 assert {k for k in a if a[k]!=b[k]}==C
 assert {k:a[k] for k in a if k not in C}==p
 assert C==set((R/'26949_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 assert not (R/'26949_ADDED_RUNTIME_PATHS.txt').read_text().strip()
 assert not (R/'26949_DELETED_RUNTIME_PATHS.txt').read_text().strip()
 root=R if '--live' in sys.argv else R/'handoff_payload_26949'
 for q in C:
  f=root/q
  assert f.exists() and hashlib.sha256(f.read_bytes()).hexdigest()==b[q],q
 if '--live' in sys.argv:
  for q,h in b.items():assert hashlib.sha256((R/q).read_bytes()).hexdigest()==h,q
 print('PASS 26949 actual 26948 authority manifest, 2051 protected, 3 changed B OFF and version, source exact')
if __name__=='__main__':main()
