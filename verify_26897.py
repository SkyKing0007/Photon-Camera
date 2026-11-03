#!/usr/bin/env python3
"""Photon 26897 exact 26895 compiled-authority DNG independence validator.
All source comparisons use the real 2025-byte-universe snapshots, not repo app/src.
"""
from pathlib import Path
import hashlib,sys,subprocess,shutil,tempfile,re
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def hashes(n):
 d={}
 for line in (R/n).read_text().splitlines():
  a,b=line.split('  ',1);assert b not in d and re.fullmatch('[a-f0-9]{64}',a)
  d[b]=a
 return d
OLD=hashes('26897_BASE_FULL_APP.sha256');NEW=hashes('26897_EXPECTED_CANDIDATE_FULL_APP.sha256');PRO=hashes('26897_UNCHANGED_PROTECTED.sha256')
ALW=sorted((R/'26897_CHANGED_ALLOWLIST.txt').read_text().splitlines());P=R/'handoff_payload_26897'
assert len(OLD)==len(NEW)==2025 and len(PRO)==2022
assert sorted(set(OLD)|set(NEW))==sorted(OLD)==sorted(NEW)
assert sorted(p for p in OLD if OLD[p]!=NEW[p])==ALW
assert ALW==['app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java','app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt','app/version.properties']
assert all(OLD[p]==NEW[p]==h for p,h in PRO.items())
assert not (R/'26897_ADDITIONS.txt').read_bytes() and not (R/'26897_DELETIONS.txt').read_bytes()
assert {str(f.relative_to(P)) for f in P.rglob('*') if f.is_file()}=={x[4:] for x in ALW}
assert all(H(P/p[4:])==NEW[p] for p in ALW)
assert 'VERSION_NAME=0.9726897' in (P/'version.properties').read_text()
assert 'VERSION_BUILD=26897' in (P/'version.properties').read_text()
def checked(src,expected):
 d={p.relative_to(src).as_posix():H(p) for p in (src/'app').rglob('*') if p.is_file()}
 assert len(d)==len(expected)==2025 and d==expected,(len(d),len(expected),[(p,d.get(p),expected.get(p)) for p in expected if d.get(p)!=expected[p]][:8])
def candidate(base,cand,transform=False):
 checked(base,OLD)
 if transform:
  assert not cand.exists(),f'candidate already exists {cand}'
  shutil.copytree(base,cand)
  for p in ALW:shutil.copy2(P/p[4:],cand/p)
 checked(cand,NEW)
 print('PASS 26897 actual compiled authority->candidate 2025 byte-identical SHA, 3 changed, 2022 protected')
def semantics(base,cand):
 checked(base,OLD);checked(cand,NEW)
 b=(cand/ALW[1]).read_text();h=(cand/ALW[0]).read_text()
 a=(base/ALW[1]).read_text();oldh=(base/ALW[0]).read_text()
 checks=[
 ('API old Night/A callers preserved', '@JvmOverloads' in b and 'earlyDngPublisher: EarlyDngPublisher? = null' in b),
 ('only direct B invokes early DNG publication',b.count('if (nativeB26868 && earlyDngPublisher != null)')==1),
 ('immutable normal DNG frame/metadata validated', 'DNG independent NORMAL population mismatch' in b and 'DNG independent noise/support invalid' in b),
 ('native B entered only after independent DNG',b.index('earlyDngPublisher.publish(originalDng)')<b.index('val stackB26856 = fusion.processFrames(frames)')),
 ('A GL completed and sticky errors logged before B', 'IRIS_DNG_A_TO_B_PRIOR_GL_ERROR' in b and 'IRIS_DNG_A_TO_B_GL_HANDOFF' in b),
 ('bridge failure frees unhanded A DNG', 'ownedIndependentDngForCleanup?.let' in b and 'ownedIndependentDngForCleanup = null' in b),
 ('early DNG requires DNG toggle',h.count('saveRAW >= 1 ? originalDng ->')==1),
 ('original normalized16 DNG writer retained', 'ImageSaver.Util.saveNormalized16StackedRaw(' in h and 'originalDng.getNormalStackedDngNoiseProfile()' in h),
 ('original true2x DNG writer retained', 'IrisSabreSuperResDngWriter.write(' in h and 'originalDng.getTrue2xWidth()' in h),
 ('raw-only failure cannot cancel successful DNG', 'saveRAW == 2 &&' in h and 'mIrisDngIndependentSaved' in h and 'IRIS_DNG_INDEPENDENT_RAW_ONLY_B_FAILURE_IGNORED' in h),
 ('JPEG+DNG DNG never re-published', '!mIrisDngIndependentAttempted' in h and 'iris26826DeferredDngTask = () ->' in h),
 ('existing A/Night algorithm and DNG writer protected', 'fun reconstruct(' in b and 'IRIS_26868_B_EXISTING_A_DNG_ONLY' in b),
 ]
 for label,v in checks:
  assert v,label
 # Historical producer mathematics and byte saver source entirely unchanged.
 for k in PRO:
  if ('Dng' in k or 'DNG' in k or 'ImageSaver.java' in k or 'AmazeGlVulkanJni.cpp' in k or 'RawStackContracts' in k):
   assert OLD[k]==NEW[k]
 assert 'IRIS_DNG_INDEPENDENT_PRE_B_PUBLISHED' not in oldh and 'IRIS_DNG_INDEPENDENT_PRE_B' not in a
 print('PASS 26897 independent DNG path, raw-only/RAW+JPEG, GL error isolation, original writer/DNG/Night intact')
def patch(base,cand,forward,rollback):
 checked(base,OLD);checked(cand,NEW)
 for n in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='iris26897_patch_') as td:
   t=Path(td);x=t/'base';x.mkdir()
   for p in ALW:
    f=x/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/p,f)
   for patch_path in (forward,rollback):assert patch_path.is_file()
   def run(args):
    r=subprocess.run(['git','-c',f'core.abbrev={n}','-C',str(x),'apply',*args],capture_output=True,text=True)
    assert r.returncode==0,(args,r.stdout,r.stderr)
   run(['--check',str(forward)]);run([str(forward)])
   for p in ALW:assert (x/p).read_bytes()==(cand/p).read_bytes()
   run(['--check',str(rollback)]);run([str(rollback)])
   for p in ALW:assert (x/p).read_bytes()==(base/p).read_bytes()
 print('PASS 26897 exact 4-operand patch CLI forward+rollback full index core.abbrev 7/12/40 fuzz0')
def tamper(base,cand):
 checked(base,OLD);checked(cand,NEW)
 with tempfile.TemporaryDirectory(prefix='iris26897_tamper_') as td:
  q=Path(td)/'q';shutil.copytree(cand,q)
  p=q/ALW[1];p.write_bytes(p.read_bytes()+b'\n// NEGATIVE TAMPER\n')
  try:checked(q,NEW)
  except AssertionError:pass
  else:raise AssertionError('tamper not rejected')
 print('PASS 26897 negative source tamper detection')
if __name__=='__main__':
 argv=sys.argv[1:];assert argv
 mode=argv[0]
 if mode=='candidate':
  assert len(argv) in (3,4);candidate(Path(argv[1]),Path(argv[2]),len(argv)==4 and argv[3]=='--transform')
 elif mode=='semantics':
  assert len(argv)==3;semantics(Path(argv[1]),Path(argv[2]))
 elif mode=='patch':
  assert len(argv)==5;patch(Path(argv[1]),Path(argv[2]),R/argv[3],R/argv[4])
 elif mode=='tamper':
  assert len(argv)==3;tamper(Path(argv[1]),Path(argv[2]))
 else:raise SystemExit('unknown verification stage '+mode)
