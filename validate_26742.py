#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26742.py BASE26741 CAND26742')
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26742_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26742 semantic validation')
