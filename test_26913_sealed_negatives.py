#!/usr/bin/env python3
"""Clean stage and SHA-resealed hostile regression (no fixture-derived authority)."""
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
R=Path(__file__).resolve().parent
STAGE1=(R/'26913_STAGE1_PATHS.txt').read_text().splitlines()
WF='.github/workflows/build-26913-change-aware.yml'
PRIOR='.github/workflows/build-26912-change-aware.yml'
FILES=STAGE1+[WF,'TRIGGER_26913.txt',PRIOR]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def must(x,msg):
 if not x:raise AssertionError('26913 sealed negative '+msg)
def seal(root):
 included=sorted(set(STAGE1)-{'26913_HANDOFF_HASHES.sha256'}|{WF,'TRIGGER_26913.txt'})
 (root/'26913_HANDOFF_HASHES.sha256').write_text(''.join(f'{sha(root/p)}  {p}\n' for p in included))
def check(root):
 return subprocess.run([sys.executable,'-S','verify_26913_handoff.py'],cwd=root,capture_output=True,text=True)
def test():
 with tempfile.TemporaryDirectory(prefix='photon_26913_negative_') as t:
  root=Path(t)
  for name in FILES:
   source=R/name
   must(source.is_file(),'missing source '+name)
   target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
  must(check(root).returncode==0,'clean proof failed: '+check(root).stderr)
  negatives=0
  def reject(label,name,data,reseal=False):
   nonlocal negatives
   f=root/name;old=f.read_bytes();hfile=root/'26913_HANDOFF_HASHES.sha256';oldh=hfile.read_bytes()
   try:
    f.write_bytes(data)
    if reseal:seal(root)
    must(check(root).returncode!=0,'accepted '+label)
    negatives+=1
   finally:
    f.write_bytes(old);hfile.write_bytes(oldh)
   must(check(root).returncode==0,'failed to restore '+label)
  source='handoff_payload_26913/app/src/main/java/com/particlesdevs/photoncamera/capture/Iris26909ShutterIsoMath.java'
  reject('source tamper',source,(root/source).read_bytes()+b'\n//changed\n')
  reject('source re-sealed tamper',source,(root/source).read_bytes()+b'\n//changed\n',True)
  reject('source version re-sealed tamper','handoff_payload_26913/app/version.properties',b'VERSION_BUILD=26912\n',True)
  reject('extra YAML trigger re-sealed',WF,(root/WF).read_bytes().replace(b'      - TRIGGER_26913.txt\n',b'      - TRIGGER_26913.txt\n      - app/src/**\n'),True)
  reject('Gradle bypass re-sealed',WF,(root/WF).read_bytes().replace(b'./gradlew --no-daemon --build-cache :app:assembleDebug',b'echo fake-compile'),True)
  reject('runner authority drift re-sealed','build_26913_incremental.py',(root/'build_26913_incremental.py').read_bytes().replace(b'RUN=42534139279',b'RUN=42534139270'),True)
  reject('prior workflow changed',PRIOR,(root/PRIOR).read_bytes()+b'\n#tampered\n')
  reject('trigger re-sealed','TRIGGER_26913.txt',b'FAKE_TRIGGER\n',True)
  reject('manifest re-sealed','26913_BASE_26912_FULL_APP.sha256',(root/'26913_BASE_26912_FULL_APP.sha256').read_bytes().replace(b'app/version.properties',b'app/version.properties.bak'),True)
  reject('allowlist re-sealed','26913_CHANGED_RUNTIME_ALLOWLIST.txt',(root/'26913_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes().replace(b'app/version.properties\n',b''),True)
  p=root/source;original=p.read_bytes();p.unlink()
  must(check(root).returncode!=0,'missing runtime overlay accepted');negatives+=1
  p.write_bytes(original)
  print('PASS 26913 clean packet and',negatives,'hostile mutation negatives including re-sealed code/YAML/authority')
if __name__=='__main__':test()
