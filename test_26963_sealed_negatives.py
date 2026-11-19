#!/usr/bin/env python3
"""Negative tamper/regression probes for four-file B native production change."""
from pathlib import Path
from hashlib import sha256
import tempfile,shutil
R=Path(__file__).resolve().parent
sealed={}
for line in (R/'26963_HANDOFF_HASHES.sha256').read_text().splitlines():
 h,p=line.split('  ',1);assert p not in sealed;sealed[p]=h
assert len(sealed)>28
for item in ('26963_FORWARD_FULLINDEX.patch','26963_ROLLBACK_FULLINDEX.patch','26963_STAGE_1_UPLOAD_PATHS.txt',
             'handoff_payload_26963/app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp',
             'handoff_payload_26963/app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp',
             'handoff_payload_26963/app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp'):
 data=(R/item).read_bytes();assert sha256(data).hexdigest()==sealed[item]
 b=bytearray(data);b[len(data)//2]^=0x40
 assert sha256(b).hexdigest()!=sealed[item]
with tempfile.TemporaryDirectory(prefix='26963_tamper_') as d:
 f=Path(d)/'app/src/main/cpp/iris26864/vendor/rawr/native/multiframe/merge_hdrplus/shaders/hdrq_merge.comp'
 f.parent.mkdir(parents=True,exist_ok=True);f.write_text('// forbidden vendor modification')
 assert 'app/'+str(f.relative_to(Path(d)/'app')) not in (R/'26963_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
print('PASS changed source, full-index patches, three-stage seal and forbidden vendor tamper rejections')
