#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: validate_26737.py BASE26736 CAND26737')
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26737_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26737 semantic validation')
