#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26743.py BASE26742 CAND26743')
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26743_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26743 semantic validation')
