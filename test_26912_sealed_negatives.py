#!/usr/bin/env python3
"""Actual staged 26912 packet positive and hostile re-sealed negative replay.
Kept independent from Android compilers, which remain mandatory in Actions.
"""
import hashlib,pathlib,shutil,subprocess,sys,tempfile
R=pathlib.Path(__file__).resolve().parent
STAGE1=(R/'26912_STAGE1_PATHS.txt').read_text().splitlines()
PROOF='.github/workflows/build-26912-change-aware.yml'
PRIOR='.github/workflows/build-26911-change-aware.yml'
ALL=STAGE1+[PROOF,'TRIGGER_26912.txt',PRIOR]
def must(ok,what):
 if not ok:raise AssertionError('26912 negative replay: '+what)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def seal(root):
 files=sorted(set(STAGE1)-{'26912_HANDOFF_HASHES.sha256'}|{PROOF,'TRIGGER_26912.txt'})
 (root/'26912_HANDOFF_HASHES.sha256').write_text(''.join(f'{sha(root/p)}  {p}\n' for p in files))
def run(root):
 return subprocess.run([sys.executable,'-S','verify_26912_handoff.py'],cwd=root,
                       capture_output=True,text=True)
def test():
 with tempfile.TemporaryDirectory(prefix='26912_negative_') as tmp:
  t=pathlib.Path(tmp)
  for name in ALL:
   source=R/name;must(source.is_file(),'missing original stage '+name)
   target=t/name;target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(source,target)
  initial=run(t)
  must(initial.returncode==0,'clean stage fails verification '+initial.stderr)
  count=0
  def negative(name,relative,payload,reseal=False):
   nonlocal count
   p=t/relative;old=p.read_bytes()
   original_seal=(t/'26912_HANDOFF_HASHES.sha256').read_bytes()
   try:
    p.write_bytes(payload)
    if reseal:seal(t)
    outcome=run(t)
    must(outcome.returncode != 0,'hostile mutation silently accepted '+name)
    count+=1
   finally:
    p.write_bytes(old)
    (t/'26912_HANDOFF_HASHES.sha256').write_bytes(original_seal)
   must(run(t).returncode==0,'restored packet no longer valid '+name)
  payload='handoff_payload_26912/app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java'
  negative('source altered',payload,(t/payload).read_bytes()+b'\n// TAMPER\n')
  negative('source altered and hostile SHA reseal',payload,(t/payload).read_bytes()+b'\n// TAMPER\n',True)
  negative('extra workflow path re-sealed',PROOF,
           (t/PROOF).read_bytes().replace(b'      - TRIGGER_26912.txt\n',
                       b'      - TRIGGER_26912.txt\n      - app/src/**\n'),True)
  negative('workflow assembly removed re-sealed',PROOF,
           (t/PROOF).read_bytes().replace(b'./gradlew --no-daemon --build-cache :app:assembleDebug',
           b'echo fake-assemble'),True)
  negative('malicious historical authority builder re-sealed','build_26912_incremental.py',
           (t/'build_26912_incremental.py').read_bytes().replace(b'BUILDER_SHA=\'1032f0f32b60452e875524973de754f965103f76b51c6a1778beb77927f0c19f\'',
           b'BUILDER_SHA=\''+b'0'*64+b'\''),True)
  negative('prior 26911 workflow mutated',PRIOR,(t/PRIOR).read_bytes()+b'\n# modified history\n')
  negative('root trigger changed and re-sealed','TRIGGER_26912.txt',b'OTHER_TRIGGER\n',True)
  negative('allowlist changed and re-sealed','26912_CHANGED_RUNTIME_ALLOWLIST.txt',
           (t/'26912_CHANGED_RUNTIME_ALLOWLIST.txt').read_bytes().replace(b'app/version.properties\n',b''),True)
  negative('source base manifest changed and re-sealed','26912_BASE_26911_FULL_APP.sha256',
           (t/'26912_BASE_26911_FULL_APP.sha256').read_bytes().replace(b'app/version.properties',b'app/version.properties.bak'),True)
  # Missing a SHA-sealed stage is a hard fail, not a nonfatal warning.
  p=t/payload;p.unlink()
  must(run(t).returncode!=0,'missing runtime source silently accepted')
  count+=1
  print(f'PASS 26912 sealed package clean replay + {count} hostile mutation rejections (including re-sealed YAML path/assemble/authority/scope)')
if __name__=='__main__':test()
