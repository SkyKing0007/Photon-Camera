#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26739.py BASE26738 CAND26739')
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26739_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26739 semantic validation')
