#!/usr/bin/env python3
"""26880 SHA-pinned root-only staging, real compiled-authority candidate-first.
Never copy flat files into repository app/src; protected actual compiled candidate
is reconstructed and frozen by unchanged inherited 17-stage runner.
"""
from pathlib import Path
from hashlib import sha256
import zlib
ROOT=Path(__file__).resolve().parent
sha=lambda data:sha256(data).hexdigest()

def parse(name):
 return {p:h for h,p in (line.split('  ',1) for line in (ROOT/name).read_text().splitlines())}
allowed=(ROOT/'26880_CHANGED_ALLOWLIST.txt').read_text().splitlines()
expected=parse('26880_NEW_CHANGED_SHA256.txt')
assert len(allowed)==34 and allowed==sorted(set(allowed)) and set(allowed)==set(expected)
assert len({Path(p).name for p in allowed})==34
for rel in allowed:
 dst=ROOT/'handoff_payload_26880'/rel
 if rel.endswith('.so'):
  packed=ROOT/'libunspektrawesome_vulkan.so.zlib'
  pin=parse('26880_ORIGINAL_NATIVE_ZLIB_SHA256.txt')
  assert pin=={'libunspektrawesome_vulkan.so.zlib':sha(packed.read_bytes())}
  data=zlib.decompress(packed.read_bytes())
  assert sha(data)=='e07838d8aa06c08038189454160293a37446a44fac998186755e93fde6e59fd1'
 else:
  src=ROOT/Path(rel).name
  assert src.is_file() and not src.is_symlink()
  data=src.read_bytes()
 assert sha(data)==expected[rel],('source hash drift',rel)
 if dst.exists():
  assert dst.read_bytes()==data,('pre-existing staged runtime collision',rel)
 else:
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_bytes(data)
 assert sha(dst.read_bytes())==expected[rel]
assert {p.relative_to(ROOT/'handoff_payload_26880').as_posix() for p in (ROOT/'handoff_payload_26880').rglob('*') if p.is_file()}==set(allowed)
assert parse('26880_PAYLOAD_SHA256.txt')=={'handoff_payload_26880/'+p:expected[p] for p in allowed}
validators={
 '26877_runtime_ownership_spektra.py':'493253d77e249aa3a921d2501a5467832a0dd5d5f1c8713b5bcbd022442cecb5',
 '26878_runtime_ownership_spektra.py':'4523ea5cecfa85672fd530442a729b72c73238a9049e8aa91a456d5778245ae1',
 '26879_runtime_ownership_spektra.py':'60fa0a85a9606115e6fdd92d283e87a43abf87a9f5e51f0f661e476f351ffa26',
}
for n in ('26880_runtime_ownership_spektra.py','26880_wr_no_fit_optional_wavelet.py'):
 validators[n]=sha((ROOT/n).read_bytes())
for name,pin in validators.items():
 src=ROOT/name
 assert src.is_file() and sha(src.read_bytes())==pin,('missing/altered historical regression',name)
 dst=ROOT/'regressions'/name
 if dst.exists():assert dst.read_bytes()==src.read_bytes(),('regression destination collision',name)
 else:dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
assert len([p for p in (ROOT/'handoff_payload_26880').rglob('*') if p.is_file()])==34
print('PASS 26880 root-only SHA-sealed 34 runtime paths, 1 original native binary, 5 regressions, exact destination')
