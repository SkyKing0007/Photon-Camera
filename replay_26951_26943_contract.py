#!/usr/bin/env python3
"""Run historical 26943 shader assertions on its original sealed payload; preserve its executable body."""
import hashlib,subprocess,sys
from build_26951_incremental import R,fail
SOURCE=R/'test_26943_shader_contract.py'
GIT_SHA='9c885f00d61952b9d85ada7b2022cd0ba3e4bb2f'
OLD="source_root=R if live else R/'handoff_payload_26943'"
NEW="source_root=R/'handoff_payload_26943'"
def main():
 b=SOURCE.read_bytes();git=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
 if git!=GIT_SHA:fail('26943 historical contract changed')
 code=b.decode()
 if code.count(OLD)!=1 or NEW in code:fail('old native ABI preflight unexpected')
 subprocess.run([sys.executable,'-S',str(SOURCE),'--payload'],cwd=R,check=True)
 revised=code.replace(OLD,NEW,1)
 if revised.replace(NEW,OLD,1)!=code:fail('historical 26943 source rewritten')
 subprocess.run([sys.executable,'-S','test_26951_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','-c',revised,'--live','--extract'],cwd=R,check=True)
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
