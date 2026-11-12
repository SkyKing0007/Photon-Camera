#!/usr/bin/env python3
"""Mutation test every staged byte; no stale or unused SHA-sealed source refs."""
from pathlib import Path
import tempfile,shutil
import verify_26920_handoff as v
R=Path(__file__).resolve().parent
paths=(R/v.STAGE).read_text().splitlines()+[v.WF,'TRIGGER_26920.txt','build_26917_incremental.py']
with tempfile.TemporaryDirectory(prefix='26920_active_negative_') as td:
 root=Path(td)
 for p in paths:
  src=R/p;assert src.is_file(),p
  q=root/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,q)
 original=v.R;v.R=root
 try:
  v.verify()
  mutated=0
  for p in paths:
   if p==v.HASHES:continue
   q=root/p;contents=q.read_bytes();q.write_bytes(contents+b'\n!tamper')
   try:
    try:v.verify()
    except (AssertionError,ValueError,FileNotFoundError):pass
    else:raise RuntimeError('MUTATED SEALED FILE ACCEPTED: '+p)
    mutated+=1
   finally:q.write_bytes(contents)
  q=root/v.HASHES;original_bytes=q.read_bytes();q.write_bytes(original_bytes+b'bad line\n')
  try:
   try:v.verify()
   except (AssertionError,ValueError,FileNotFoundError):pass
   else:raise RuntimeError('MUTATED SHA INDEX ACCEPTED')
  finally:q.write_bytes(original_bytes)
  v.verify()
  print('PASS 26920 V2 '+str(mutated+1)+' hostile staged-file mutations fail closed')
 finally:v.R=original
