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
  # Both unconditional buffer interfaces must survive even a RESEALED
  # malformed native descriptor. Test each pipeline independently.
  native=root/'handoff_payload_26920/app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/pipeline/src/VulkanExecutor.cpp'
  original_native=native.read_bytes(); original_manifest=man.read_bytes()
  for current,next_shader,slot in [(b'lk_refine',b'flow_dense_smooth',4),
                                   (b'robust_photometric',b'robust_erode5',9)]:
   prefix,rest=original_native.split(b'{"'+current+b'",',1)
   section,suffix=rest.split(b'{"'+next_shader+b'",',1)
   old_binding=('{%d, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}'%slot).encode()
   new_binding=('{%d, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}'%slot).encode()
   bad_section=section.replace(old_binding,new_binding)
   assert bad_section!=section
   broken_native=prefix+b'{"'+current+b'",'+bad_section+b'{"'+next_shader+b'",'+suffix
   native.write_bytes(broken_native)
   before=hashlib.sha256(original_native).hexdigest().encode()
   after=hashlib.sha256(broken_native).hexdigest().encode()
   assert original_manifest.count(before)==1
   man.write_bytes(original_manifest.replace(before,after))
   try:
    try:v.verify()
    except AssertionError:pass
    else:raise RuntimeError('RESEALED Vulkan descriptor mismatch accepted for '+current.decode())
   finally:
    native.write_bytes(original_native)
    man.write_bytes(original_manifest)
  v.verify()
  # Regression for actual 26920 V4 phone crash: the compiled B OFF HDRq
  # CMake shadow overwrote both V4-corrected vendor files. Independently
  # reseal each shadow defect and insist the semantics reject it.
  semantic_cases=[
   ('handoff_payload_26920/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
    b'// 26920 ABI: the active LK shader unconditionally declares set0 binding4.\n                                    {4, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}',
    b'// 26920 ABI: the active LK shader unconditionally declares set0 binding4.\n                                    {4, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}'),
   ('handoff_payload_26920/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp',
    b'// 26920 ABI: the photometric shader unconditionally declares set0 binding9.\n                                    {9, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER}',
    b'// 26920 ABI: the photometric shader unconditionally declares set0 binding9.\n                                    {9, VK_DESCRIPTOR_TYPE_STORAGE_IMAGE}'),
   ('handoff_payload_26920/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
    b'if (merge_.iris26920Active) ensureHostBuffer(iris26920Counts_, 16u);',
    b'if (false) ensureHostBuffer(iris26920Counts_, 16u);'),
   ('handoff_payload_26920/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp',
    b'result.iris26920Enabled = true;', b'result.iris26920Enabled = false;'),
  ]
  for target,good,bad in semantic_cases:
   path=root/target
   before=path.read_bytes();original_manifest=man.read_bytes()
   assert before.count(good)==1,(target,good)
   changed=before.replace(good,bad)
   path.write_bytes(changed)
   h1=hashlib.sha256(before).hexdigest().encode()
   h2=hashlib.sha256(changed).hexdigest().encode()
   assert original_manifest.count(h1)==1
   man.write_bytes(original_manifest.replace(h1,h2))
   try:
    try:v.verify()
    except AssertionError:pass
    else:raise RuntimeError('RESEALED 26920 V4 CMAKE SHADOW REGRESSION ACCEPTED: '+target)
   finally:
    path.write_bytes(before);man.write_bytes(original_manifest)
  v.verify()
  print('PASS 26920 V5 '+str(mutated+8)+' hostile staged mutations incl resealed optimizer CLI, vendor and CMake-shadow Vulkan ABI defects fail closed')
 finally:v.R=original
