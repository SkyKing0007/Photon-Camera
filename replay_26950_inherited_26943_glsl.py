#!/usr/bin/env python3
"""Replay untouched successful 26943 real GLSL/SPIR-V compiler body."""
import subprocess,hashlib,sys
from build_26950_incremental import R,fail
ORIG=R/'compile_26943_shaders.sh'
GIT='95cecfd9a98a5a3a8ab3154e785e1d708f9dd876'
OLD='python3 -S test_26943_shader_contract.py --live --extract'
NEW='python3 -S replay_26950_26943_contract.py --live --extract'
def main():
 b=ORIG.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
 if blob!=GIT or b.decode().count(OLD)!=1:fail('26943 original shell no longer exact')
 script=b.decode().replace(OLD,NEW,1)
 if script.replace(NEW,OLD,1)!=b.decode():fail('26943 compiler changed beyond historical gate')
 subprocess.run(['bash','-c',script,str(ORIG)],cwd=R,check=True)
 print('PASS historical 26943 full real shader compiler replay with sealed old ABI')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
