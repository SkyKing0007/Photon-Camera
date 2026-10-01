#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26741.py BASE26740 CAND26741')
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26741_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26741 semantic validation')
