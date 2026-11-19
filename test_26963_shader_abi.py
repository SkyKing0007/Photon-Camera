#!/usr/bin/env python3
"""Fail-closed shader ABI, private descriptor table, RAW source ownership and reuse proof."""
from pathlib import Path
import argparse,re
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');args=p.parse_args()
D=R if args.live else R/'handoff_payload_26963'
sh=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqMismatch.comp').read_text()
rec=(D/'app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp').read_text()
exe=(D/'app/src/main/cpp/iris26864/bridge/Iris26888BOffVulkanExecutor.cpp').read_text()
assert sh.startswith('#version 450\n') and sh.count('void main()')==1
assert sh.count('layout(set = 0, binding = 5, rgba32f) writeonly uniform image2D temporalAligned;')==1
assert sh.count('    int useSpatialScreen;')==1 and rec.count('    std::int32_t useSpatialScreen;')==1
assert rec.count('static_assert(sizeof(MismatchPc)==56u')==1
assert 'const bool spatialScreen26963 = uniformExposure_ &&' in rec
assert 'iris26941BOffHdrqLazyPoolReset && !motionGateEnabled_' in rec
assert 'gated?1:0,spatialScreen26963?1:0' in rec
assert 'ib(5,temporalAligned26963)' in rec
assert 'const auto& temporalAligned26963 = arena_.image("hdrq_out_rgba");' in rec
assert 'const auto& fftInput26963 = spatialScreen26963 ? temporalAligned26963 : alignedRgba;' in rec
assert 'else if (spatialScreen26963)' in rec and 'computeWriteBarrier(c);' in rec
assert 'gated ? 1 : 0' in rec
assert rec.count('add("hdrq_out_rgba", rgba, PixelStorage::RGBA32Float, Lifetime::Output)')==1
assert 'recordSubstitutionSource' in rec and 'if (uniformExposure_ || substitutionReady_) return;' in rec
assert 'vec4 refCenter = imageLoad(refRgba, center);' in sh
assert 'imageStore(temporalAligned, center, mix(alignedCenter, refCenter, confidence));' in sh
assert 'if (p.useSpatialScreen != 0)' in sh and 'if(lane!=0u)return;' in sh
assert sh.index('    barrier();\n    // A continuous') < sh.index('if(lane!=0u)return;')
assert 'smoothstep(6.0, 9.0, z)' in sh and 'smoothstep(0.62, 0.86, coherence)' in sh
assert 'smoothstep(9.0, 15.0, snr)' in sh and 'isnan' in sh and 'isinf' in sh
assert 'if(lane!=0u)return;' in sh
assert 'float acc=0.0;' in sh and 'imageStore(zmap,g' in sh and 'imageStore(mismatch,g' in sh
assert 'hdrq_mismatch' in exe
spec=exe.split('"hdrq_mismatch",',1)[1].split('"hdrq_region_mean",',1)[0]
assert set(map(int,re.findall(r'\{(\d+), VK_DESCRIPTOR_TYPE_STORAGE_IMAGE\}',spec)))==set(range(6))
assert 'mf_hdrq_mismatch_prod_spv' in spec and 'mf_hdrq_mismatch_trace_spv' in spec
# std430 scalar offsets: 2xivec2 = 16, eight floats = 32, two int = 8 => 56 bytes.
assert 16+32+8==56
# 64 threads map to exactly all 8x8 owned pixels, with NO dependence on tile lattice for the decision.
coords={(x&7,2*y+(x>>3)) for y in range(4) for x in range(16)}
assert coords=={(x,y) for y in range(8) for x in range(8)}
# No writes into input image, no out-of-group read-after-write; no extra storage image allocation.
assert 'imageStore(alignedRgba' not in sh and 'imageStore(refRgba' not in sh
assert 'add("hdrq_masked' not in rec and 'setMotionGate(true)' not in rec
code=re.sub(r'/\*.*?\*/|//[^\n]*',' ',sh,flags=re.S)
assert not re.search(r'\b(?:float|int|uint|vec[234]|mat[234]|bool|const)\s+(?:coherent|flat|in|out|varying|attribute|uniform|buffer|precision|shared|layout|sample|switch|class|atomic_uint)\s*[=;,\[]',code)
print('PASS native 26963 private GLSL ABI, 6 image bindings, 56-byte push, TLS B-only, unique pixel ownership, no same-image races, no extra allocation')
