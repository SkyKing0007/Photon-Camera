#!/usr/bin/env python3
"""Mutation test every staged byte; no stale or unused SHA-sealed source refs."""
from pathlib import Path
import tempfile,shutil,hashlib
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
  # Regression for the actual failed 26920 V2 Actions job 130937798460:
  # change a VALID optimizer CLI to the malformed old --target-env vulkan1.1
  # and also RESEAL it. The semantic gate MUST still reject the package.
  sh=root/'compile_26920_lk_shaders.sh'
  man=root/v.HASHES
  original_script=sh.read_bytes()
  original_manifest=man.read_bytes()
  broken=original_script.replace(b'spirv-opt --target-env=vulkan1.1 -O ',
                                 b'spirv-opt --target-env vulkan1.1 -O ')
  assert broken!=original_script
  sh.write_bytes(broken)
  old_hash=hashlib.sha256(original_script).hexdigest().encode('ascii')
  new_hash=hashlib.sha256(broken).hexdigest().encode('ascii')
  assert original_manifest.count(old_hash)==1
  man.write_bytes(original_manifest.replace(old_hash,new_hash))
  try:
   try:v.verify()
   except AssertionError:pass
   else:raise RuntimeError('RESEALED 26904 V1 optimizer CLI accepted')
  finally:
   sh.write_bytes(original_script)
   man.write_bytes(original_manifest)
  v.verify()
  v.verify()
  print('PASS 26920 V3 '+str(mutated+2)+' hostile staged-file mutations incl resealed optimizer CLI fail closed')
 finally:v.R=original
