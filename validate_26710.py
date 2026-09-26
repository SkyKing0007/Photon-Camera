#!/usr/bin/env python3
import subprocess,sys
subprocess.run([sys.executable,str(__import__('pathlib').Path(__file__).with_name('verify_26710_regressions.py')),sys.argv[1],sys.argv[2]],check=True)
print('PASS 26710 semantic validation')
