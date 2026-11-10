#!/usr/bin/env python3
"""Exact 26916 compiled authority and 26917 B HDRq-only staged 7 + generated 1.
Semantic checks cannot substitute for the mandatory real GLSL/CMake/NDK/Java/
Kotlin and full Android compilation in the inherited Actions job.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
LIVE='--live' in sys.argv
ROOT=R if LIVE else R/'handoff_payload_26917'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 d={}
 for line in (R/name).read_text().splitlines():
  h,p=line.split('  ',1)
  assert re.fullmatch('[a-f0-9]{64}',h) and p.startswith('app/') and '..' not in Path(p).parts and p not in d
  d[p]=h
 return d
base=manifest('26917_BASE_26916_FULL_APP.sha256')
pre=manifest('26917_PRECOMPILE_EXPECTED_FULL_APP.sha256')
staged=(R/'26917_STAGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
allowed=(R/'26917_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
generated=(R/'26917_GENERATED_RUNTIME_PATHS.txt').read_text().splitlines()
added=(R/'26917_ADDED_RUNTIME_PATHS.txt').read_text().splitlines()
deleted=(R/'26917_DELETED_RUNTIME_PATHS.txt').read_text().splitlines()
assert len(base)==len(pre)==2036 and base.keys()==pre.keys()
assert not added and not deleted and len(staged)==7 and len(allowed)==8 and len(generated)==1
assert len(set(staged))==7 and len(set(allowed))==8 and len(set(generated))==1
assert set(staged)|set(generated)==set(allowed)
assert {p for p in base if base[p]!=pre[p]}==set(staged)
assert all(base[p]==pre[p] for p in base if p not in staged)
assert generated==['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_import.spv']
assert 2036-len(allowed)==2028
for p in staged:
 assert (ROOT/p).is_file() and sha(ROOT/p)==pre[p],p
if LIVE:
 actual={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'app/src').rglob('*') if p.is_file()}
 for p in ('app/build.gradle','app/version.properties'):actual[p]=sha(ROOT/p)
 assert actual==pre,{'missing':sorted(pre.keys()-actual.keys())[:5],
                      'extra':sorted(actual.keys()-pre.keys())[:5],
                      'wrong':[p for p in pre if actual.get(p)!=pre[p]][:8]}
header=(ROOT/'app/src/main/cpp/iris26856/amaze/include/amaze/Amaze.hpp').read_text()
pipeline=(ROOT/'app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp').read_text()
shader=(ROOT/'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp').read_text()
entry=(ROOT/'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc').read_text()
assert 'bool phaseSafePhysicalHalo = false;' in header
assert 'tileGrid(cfg.width, cfg.height, cfg.phaseSafePhysicalHalo)' in pipeline
assert 'p.reserved = cfg.phaseSafePhysicalHalo ? 1.0f : 0.0f;' in pipeline
assert 'static_assert(sizeof(TileParams) == 144' in pipeline
assert shader.count('iris26917ReflectPhysicalBayer(')==3
assert 'if (tile.reserved > 0.5)' in shader
assert shader.count('textureSize(packedInput, 0) * 2')==1
assert 'config.phaseSafePhysicalHalo=(!sr && photoBOffOnly == JNI_TRUE);' in entry and entry.count('phaseSafePhysicalHalo')==1
assert 'config.inputMode=amaze::InputMode::PackedCfaRgba16fImage;' in entry
assert entry.count('jboolean photoBOffOnly')==2 and 'physicalLensIdentity,javaBOffNoise,photoBOffOnly);' in entry
java=(ROOT/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java').read_text()
kotlin=(ROOT/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert java.count('boolean photoBOffOnly')==2
assert 'photoBOffOnly && !wronskiTrue2x' in java
assert 'false, // Wronski B SR ON never owns physical-halo experiment.' in kotlin
assert '!parameters.iris26903NightB && !parameters.irisNightActive' in kotlin
assert (ROOT/'app/version.properties').read_text().count('VERSION_BUILD=26917')==1
assert 'VERSION_NAME=0.9726917' in (ROOT/'app/version.properties').read_text()
for p in base:
 if p not in staged and any(x in p for x in ('/vendor/','/jniLibs/','MotionV2PreviewHueCalibration.java','preview_hue_match_26907.glsl','amaze_export.comp')):
  assert base[p]==pre[p],p
print('PASS 26917 '+('live actual 26916 authority-seeded' if LIVE else 'SHA-sealed payload')+' B OFF source: 2036, staged 7, generated SPV 1, protected 2028')
