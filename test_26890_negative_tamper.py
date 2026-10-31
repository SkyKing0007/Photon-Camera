#!/usr/bin/env python3
"""Mutate actual frozen 26890 candidate and one protected file; verifier MUST fail."""
import pathlib,hashlib,subprocess,sys,tempfile,shutil
assert len(sys.argv)==3,'base candidate'
B=pathlib.Path(sys.argv[1]);C=pathlib.Path(sys.argv[2]);R=pathlib.Path(__file__).resolve().parent
allowed=(R/'26890_CHANGED_ALLOWLIST.txt').read_text().splitlines()
with tempfile.TemporaryDirectory(prefix='photon26890_tamper_') as tmp:
 w=pathlib.Path(tmp)/'candidate';shutil.copytree(C,w)
 for p in allowed+['app/src/main/assets/analyze_lut.png']:
  file=w/p;original=file.read_bytes()
  file.write_bytes(original+b'\nTAMPER26890\n')
  v=subprocess.run([sys.executable,'-S',str(R/'verify_26890_candidate.py'),str(B),str(w)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  assert v.returncode!=0,('candidate tamper accepted',p)
  file.write_bytes(original)
 v=subprocess.run([sys.executable,'-S',str(R/'verify_26890_candidate.py'),str(B),str(w)],capture_output=True,text=True)
 assert v.returncode==0,(v.stdout,v.stderr)
print('PASS 26890 9 negative candidate/protected file tamper rejections, actual source restored and reverified')
