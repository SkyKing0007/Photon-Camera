#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26740.py BASE26739 CAND26740')
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26740_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26740 semantic validation')
