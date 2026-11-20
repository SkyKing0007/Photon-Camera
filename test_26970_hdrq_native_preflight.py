#!/usr/bin/env python3
"""26970 V3 real-source native shadow regression for Actions 44807631086.

The previous compiler error was in the *generated private build copy* of the
Iris-owned HDR+ recorder, despite the pinned upstream vendor tree remaining
unchanged. Inspect the exact CMake source, physically reproduce COPYONLY, and
reject the old unused TilesPc declaration before NDK compilation. This is NOT
an NDK compile substitute: mandatory dual-ABI -Werror/Gradle gates remain.
"""
from pathlib import Path
import hashlib,re,sys,tempfile,shutil,subprocess
R=Path(__file__).resolve().parent
P=R if '--live' in sys.argv else R/'handoff_payload_26970'
rel=Path('app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp')
cmrel=Path('app/src/main/cpp/iris26864/Iris26864VendorRawr.cmake')
cpp=(P/rel).read_text()
cm=(P/cmrel).read_text()
source_abs=P/rel
prior_sha='9189ec49578dde5beca183b7b3f0d8ca8b6489c3b7f4cbc0bfa03684b65f5341' # exact failed V2 Iris-owned overlay
fixed_sha='921db1448908b02b0992f7b9bba46ebb6c2a192018c48614d1cc1ee45f762f75'
assert hashlib.sha256(source_abs.read_bytes()).hexdigest()==fixed_sha, '26970 V3 native source unexpectedly changed'
assert (R/'26970_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines().count(rel.as_posix())==1
assert 'vendor/' not in rel.as_posix()

# The failing NDK source is a generated build-shadow, not app/src vendor.
assert cm.count('"${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline/src/HdrPlusRecorder.cpp" COPYONLY)')==1
assert cm.count('"${CMAKE_CURRENT_SOURCE_DIR}/iris26864/bridge/Iris26887BOffHdrqRecorder.cpp"')==1
assert 'file(COPY "${IRIS26864_VENDOR_ROOT}/" DESTINATION "${IRIS26887_VENDOR_SHADOW}")' in cm
assert 'add_subdirectory("${IRIS26887_VENDOR_SHADOW}/multiframe/pipeline"' in cm

start='void HdrPlusFrequencyRecorder::recordPassFinish(VkCommandBuffer c, std::uint32_t frameCount) {'
assert cpp.count(start)==1

def body_after(s):
    part=s.split(start,1)[1]
    depth=1
    for i,ch in enumerate(part):
        if ch=='{':depth+=1
        elif ch=='}':
            depth-=1
            if depth==0:return part[:i]
    raise AssertionError('missing body close')

def check(s):
    b=body_after(s)
    assert not re.search(r'\bTilesPc\s+tp\s*\{',b),'unused shadow-local TilesPc tp reintroduced'
    assert b.count('Iris26970NoiseDeconvPc sidecar{')==1
    assert b.count('&sidecar, sizeof(sidecar)')==1
    assert b.count('ShaderId::HdrqDeconvolute')==1
    assert b.count('ShaderId::HdrqBackwardDft')==1
    assert b.count('ShaderId::HdrqBorder')==1
    assert b.count('ShaderId::HdrqAccumulate')==1
    assert all(re.search(r'\b'+re.escape(v)+r'\b',b) for v in ('tx','ty','frameCount','finalFt','out','sidecar'))
    assert b.count('computeWriteBarrier(c);')>=3

check(cpp)
# Keep both OTHER real TilesPc tp declarations: they are still referenced in
# reference RMS + seed DFT and in each companion forward DFT.
assert cpp.count('TilesPc tp{std::int32_t(tx), std::int32_t(ty)};')==2
assert cpp.count('&tp, sizeof(tp)')>=2

# Physically reproduce configure_file(COPYONLY) bytes in a scratch build shadow.
with tempfile.TemporaryDirectory(prefix='ph26970v3_cmake_shadow_') as td:
    root=Path(td)
    dest=root/'iris26887_b_only_vendor/native/multiframe/pipeline/src/HdrPlusRecorder.cpp'
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source_abs,dest)
    assert dest.read_bytes()==source_abs.read_bytes()
    check(dest.read_text())

# Mandatory regression: the exact declaration that failed the real NDK clang
# in run 44807631086 must be rejected before the next Android job.
needle='    const auto& out = arena_.image("hdrq_out_rgba");\n'
assert needle in body_after(cpp)
mutated=cpp.replace(needle,needle+'    TilesPc tp{std::int32_t(tx), std::int32_t(ty)};\n',1)
# The first 'out' occurs earlier; insert specifically within recordPassFinish.
prefix,post=cpp.split(start,1)
assert post.count(needle)==1
mutated=prefix+start+post.replace(needle,needle+'    TilesPc tp{std::int32_t(tx), std::int32_t(ty)};\n',1)
assert hashlib.sha256(mutated.encode()).hexdigest()==prior_sha, 'V3 fix is not exactly the single unused-line deletion from the failed V2 recorder'
try:
    check(mutated)
except AssertionError as e:
    assert 'unused shadow-local TilesPc' in str(e)
else:
    raise AssertionError('V2 failed native declaration not caught by regression')

# Validate original -Wunused-variable failure mechanism with real local Clang,
# without pretending this small fixture is the Android NDK compilation.
clang=shutil.which('clang++')
assert clang, 'real host Clang++ unavailable; native preflight must fail closed'
with tempfile.TemporaryDirectory(prefix='ph26970v3_unused_clang_') as td:
    file=Path(td)/'unused.cc'
    pre='struct TilesPc { int x,y; };\nint f() { const int tx=3,ty=4; TilesPc tp{tx,ty}; return tx+ty; }\n'
    file.write_text(pre)
    cmd=[clang,'-std=c++17','-Wall','-Wextra','-Wpedantic','-Werror','-fsyntax-only',str(file)]
    bad=subprocess.run(cmd,capture_output=True,text=True)
    assert bad.returncode!=0 and 'unused variable' in bad.stderr, bad.stderr
    file.write_text('struct TilesPc { int x,y; };\nint f() { const int tx=3,ty=4; return tx+ty; }\n')
    good=subprocess.run(cmd,capture_output=True,text=True)
    assert good.returncode==0,good.stderr
print('PASS 26970 V3 actual Iris HDRQ private CMake-shadow COPYONLY, V2 dead TilesPc NDK regression and Clang -Wunused-variable/-Werror negative+positive (host fixture only; real Android NDK required)')
