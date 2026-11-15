#!/usr/bin/env python3
"""Exact 26941 compiled -> B OFF only GPU scheduler optimization, original RAWR shaders intact."""
import sys,re
from pathlib import Path
from build_26942_incremental import R,BASE,scope,sha,fail,exact
SHADOW='app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp'
VERSION='app/version.properties'
def main():
 ch,old,new=scope()
 if ch!={SHADOW,VERSION}:fail('non-allowlisted source change')
 live='--live' in sys.argv
 root=R if live else R/'handoff_payload_26942'
 s=(root/SHADOW).read_text()
 v=(root/VERSION).read_text()
 if 'VERSION_BUILD=26942' not in v or 'VERSION_NAME=0.9726942' not in v:fail('wrong app version')
 for name in ('IRIS_26942_B_OFF_FREQUENCY_CHUNK_FUSION',
    'const bool batchPadMerge26942 = iris26941BOffHdrqLazyPoolReset &&',
    'algorithm_ == MergeAlgorithm::HdrPlusFrequency &&',
    'hdrplus_.frequencyAlignOnce && pass != 0u && !aligns;',
    'const auto batched = executeChunk(14u, i, profile ? 7u : 6u, [&] {',
    'recorder.recordCompanionAlign(command_, frames[i].raw.view,',
    'recorder.recordCompanionMerge(command_, frameCount, i,',
    'timings.companionPrepareMs += batched.second.front();',
    'timings.accumulationMs += batched.second[q];',
    'timings.accumulationMs += batched.first;',
    'if (pass == 3u) {'):
  if name not in s:fail('actual B OFF guarded GPU scheduling is missing '+name)
 # The original RAWR chunk path must remain byte-for-byte identical after
 # stripping the four-space indentation introduced by the new guarded else.
 marker='            const bool aligns = recorder.alignsThisPass();'
 fallback='            } else {\n                const bool aligns = recorder.alignsThisPass();\n'
 # Work from exact frequency function; other algorithms are untouched.
 pos=s.index('BurstRunResult AndroidBurstCoordinator::runHdrPlusFrequency(')
 f=s[pos:]
 if f.count('            if (pass == 3u) {')!=1:fail('frame release semantic changed')
 if not ('if (batchPadMerge26942) {' in f and '            } else {\n                const bool aligns =' in f):fail('original split branch absent')
 if 'vkQueueWaitIdle' in f.split('IRIS_26942_B_OFF_FREQUENCY_CHUNK_FUSION',1)[1].split('            if (pass == 3u) {',1)[0]:
  fail('B OFF optimization added new GPU-idle fence')
 # NDK V1 failure: this B OFF coordinator TU must declare (not define)
 # the TLS switch exported from the protected 26941 Vulkan executor TU.
 declaration='// Linked to the unchanged 26941 B-OFF Vulkan executor (same namespace).\n// 26942 V1 NDK failure regression: never use the TLS guard without a declaration.\nextern thread_local bool iris26941BOffHdrqLazyPoolReset;\n'
 key='thread_local std::optional<std::array<float,8>> iris26912BOffNoiseOverride;\n'
 if s.count(declaration)!=1 or s.count('extern thread_local bool iris26941BOffHdrqLazyPoolReset;')!=1:
  fail('26942 V1 undeclared native TLS symbol regression')
 if s.index(declaration)!=s.index(key)+len(key):
  fail('TLS declaration not at known 26941 native coordinator namespace scope')
 if s.index('namespace rawr::raw_gpu_pipeline {')>s.index(declaration) or s.index(declaration)>s.index('namespace {'):
  fail('TLS declaration outside external RAWR pipeline namespace')
 if live:
  exact(R,'26942_EXPECTED_FULL_APP.sha256','live 26942 source authority')
  p=BASE/SHADOW
  if not p.is_file() or sha(p)!=old[SHADOW]:fail('compiled 26941 original shadow unavailable')
  prev=p.read_text();a=prev.index(marker,prev.index('BurstRunResult AndroidBurstCoordinator::runHdrPlusFrequency('))
  z=prev.index('            if (pass == 3u) {',a)
  aa=s.index(marker,s.index('BurstRunResult AndroidBurstCoordinator::runHdrPlusFrequency('))
  zz=s.index('            if (pass == 3u) {',aa)
  if prev[:a]!=s[:aa].replace(declaration,'',1) or prev[z:]!=s[zz:]:fail('outside B OFF per-companion scheduling was altered')
  protected_old=prev[a:z]
  branch=s[s.index(fallback,aa)+len('            } else {\n'):zz]
  # Guarded else has one additional closing brace for the if/else; remove
  # only that brace, then restore original four-space indentation exactly.
  if not branch.endswith('            }\n'):fail('missing new guard closing brace')
  branch=branch[:-len('            }\n')]
  restored=''.join(line[4:] if line.startswith('    ') else line for line in branch.splitlines(keepends=True))
  if restored!=protected_old:fail('original RAWR align/merge path was modified')
  if 'const bool profile' not in protected_old or 'recordCompanionAlignCoarse' not in protected_old:
   fail('lost successful original split pass')
  # Full Kotlin/Java+native vendor/GLSL protected SHA and B-ON JNI guard are
  # enforced by exact manifest, not by a token-only surface check.
  if not set((R/'26942_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()).isdisjoint(
    {'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
     'app/src/main/assets/shaders/motionv2/gainmap.glsl',
     'app/src/main/assets/shaders/motionv2/render.glsl'}):
   fail('proven 26941 SDR/UHDR source changed')
 print('PASS original RAWR math/pass/frames/guard, new low-zoom B OFF only 3 later-pass pad+merge batching; protected files 2048')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26942 SOURCE BLOCKED',e,file=sys.stderr);sys.exit(1)
