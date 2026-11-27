#!/usr/bin/env python3
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parent;p=R/'test_26986_native_host.py';raw=p.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='9a0f29cd43ee690509847406bb8de92ca77ea970'
s=raw.decode();assert s.count('iris26985c_lkrl_2420_pipelines.bin')==1 and s.count('26986_CHANGED_RUNTIME_ALLOWLIST.txt')==1
s=s.replace('iris26985c_lkrl_2420_pipelines.bin','iris26985c_lkrl_2458_pipelines.bin').replace('26986_CHANGED_RUNTIME_ALLOWLIST.txt','26995_CHANGED_RUNTIME_ALLOWLIST.txt')
exec(compile(s,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
