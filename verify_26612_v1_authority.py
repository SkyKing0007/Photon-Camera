#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
PKG=Path(__file__).resolve().parent
COUNTS={'full':1708,'protected':1700,'native':802,'vendor':778,'dng':7}
def fail(x):raise SystemExit('FAIL: '+x)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 d={}
 for l in Path(p).read_text().splitlines():
  if l.strip():h,r=l.split('  ',1);d[r]=h
 return d
def verify(root,mf):
 m=read(mf)
 for r,h in m.items():
  p=Path(root)/r
  if not p.is_file() or sha(p)!=h:fail('authority '+r)
 return len(m)
def main():
 if len(sys.argv)!=4:fail('usage pkg base candidate')
 pkg,b,c=map(Path,sys.argv[1:])
 pairs={'full':('V1_26612_BASE_26611_V1_FULL_APP.sha256','V1_26612_EXPECTED_CANDIDATE_FULL_APP.sha256'),'protected':('V1_26612_PROTECTED_UNCHANGED_BASE.sha256','V1_26612_PROTECTED_UNCHANGED_CANDIDATE.sha256'),'native':('V1_26612_NATIVE_PROTECTED_BASE.sha256','V1_26612_NATIVE_PROTECTED_CANDIDATE.sha256'),'vendor':('V1_26612_VENDOR_PROTECTED_BASE.sha256','V1_26612_VENDOR_PROTECTED_CANDIDATE.sha256'),'dng':('V1_26612_DNG_BASE.sha256','V1_26612_DNG_CANDIDATE.sha256')}
 for lab,(bn,cn) in pairs.items():
  nb=verify(b,pkg/bn);nc=verify(c,pkg/cn)
  if nb!=COUNTS[lab] or nc!=COUNTS[lab]:fail(f'{lab} completeness {nb}/{nc}')
  if lab!='full' and (pkg/bn).read_bytes()!=(pkg/cn).read_bytes():fail(lab+' invariance')
 if verify(b,pkg/'V1_26612_PREWRITE_SOURCE_HASHES.sha256')!=8:fail('prewrite count')
 if verify(c,pkg/'V1_26612_EXPECTED_CHANGED_SOURCE_HASHES.sha256')!=8:fail('changed count')
 print('PASS successful-26611 V1 compiled-candidate authority full=1708 protected=1700 native=802 vendor=778 DNG=7')
 print('PASS exact 8-file prewrite/expected hashes; protected/native/vendor/DNG invariance')
if __name__=='__main__':main()
