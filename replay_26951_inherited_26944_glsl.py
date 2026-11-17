#!/usr/bin/env python3
"""Byte-exact successful 26944 shader compiler body with original validator run on sealed 26944 source."""
import subprocess,hashlib,sys
from build_26951_incremental import R,fail
ORIG=R/'compile_26944_shaders.sh'
GIT='7b73fe7b353fdf2e45ba2fe0a79c2b476b59cd2f'
OLD='python3 -S test_26944_shader_contract.py --live'
NEW='python3 -S test_26944_shader_contract.py --payload'
def main():
 b=ORIG.read_bytes();blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
 if blob!=GIT or b.decode().count(OLD)!=1:fail('26944 original shell no longer exact')
 script=b.decode().replace(OLD,NEW,1)
 if script.replace(NEW,OLD,1)!=b.decode():fail('26944 real compiler changed')
 subprocess.run([sys.executable,'-S','test_26944_shader_contract.py','--payload'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26951_source.py','--live'],cwd=R,check=True)
 subprocess.run(['bash','-c',script,str(ORIG)],cwd=R,check=True)
 print('PASS historical 26944 full real shader compiler, sealed old ABI')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
