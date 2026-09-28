#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
subprocess.run([sys.executable,str(Path(__file__).with_name('verify_26727_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26727 semantic validation')
