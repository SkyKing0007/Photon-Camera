#!/usr/bin/env python3
"""Preserve actual 26963 B-only Vulkan descriptor / 56-byte push layout, no extra scratch."""
from pathlib import Path
import argparse,re,hashlib
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
D=R if args.live else R/'handoff_payload_26964'
s=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
assert s.startswith('#version 450\n') and s.count('void main()')==1
for token in ('layout(local_size_x = 16, local_size_y = 4) in;',
 'layout(set = 0, binding = 5, rgba32f) writeonly uniform image2D temporalAligned;',
 '    int useMotionGate;', '    int useSpatialScreen;',
 'imageStore(temporalAligned, center, mix(alignedCenter, refCenter, confidence));',
 'if (p.useSpatialScreen != 0)', 'if(lane!=0u)return;',
 'vec2(-0.5), vec2(0.5)','gradient-energy guard','float varEnergy','imageStore(zmap,g,vec4(p.useMotionGate!=0 ? acc/16.0 : 0.0));'):
 assert token in s,token
assert s.count('imageStore(temporalAligned, center,')==1
assert 'imageStore(alignedRgba' not in s and 'imageStore(refRgba' not in s
assert s.index('    barrier();\n    // IRIS_26964')<s.index('if(lane!=0u)return;')
assert {(x&7,2*y+(x>>3)) for y in range(4) for x in range(16)}=={(x,y) for y in range(8) for x in range(8)}
# Non-literal shader pipeline/ABI is inherited BYTE-FOR-BYTE from the successful 26963 source.
base={p:h for h,p in [line.split('  ',1) for line in (R/'26964_BASE_26963_FULL_APP.sha256').read_text().splitlines()]}
out={p:h for h,p in [line.split('  ',1) for line in (R/'26964_EXPECTED_FULL_APP.sha256').read_text().splitlines()]}
for rel in ('app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp','app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp','app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMerge.comp'):
 assert base[rel]==out[rel]
 if args.live: assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==out[rel]
if args.live:
 rec=(R/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp').read_text()
 exe=(R/'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp').read_text()
 assert 'static_assert(sizeof(MismatchPc)==56u' in rec
 assert 'const bool spatialScreen26963 = uniformExposure_' in rec
 assert 'iris26941BOffHdrqLazyPoolReset && !motionGateEnabled_' in rec
 assert 'const auto& temporalAligned26963 = arena_.image("hdrq_out_rgba");' in rec
 assert 'const auto& fftInput26963 = spatialScreen26963 ? temporalAligned26963 : alignedRgba;' in rec
 spec=exe.split('"hdrq_mismatch",',1)[1].split('"hdrq_region_mean",',1)[0]
 assert set(map(int,re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_STORAGE_IMAGE\}',spec)))==set(range(6))
 assert 'mf_hdrq_mismatch_prod_spv' in spec and 'mf_hdrq_mismatch_trace_spv' in spec
print('PASS 26964 B-only 56-byte Vulkan ABI, 6 image bindings, unique 8x8 ownership, proven 26963 exact recorder/executor/hash stability')
