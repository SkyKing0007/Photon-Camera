#!/usr/bin/env python3
"""Fail-closed 26955 Actions graph, prior successful 26954 34-stage prefix, stale references and 26904 compiler regressions."""
import hashlib,re,sys,subprocess
from pathlib import Path
from build_26955_incremental import R,fail,WORKFLOW_SHA,BUILDER_SHA,TAR_SHA,ART_SHA,COMMIT,RUN,ART_ID,PRIOR_APK_SHA

def main():
 old=(R/'26954_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 new=(R/'.github/workflows/build-26955-change-aware.yml').read_text()
 if hashlib.sha256(old.encode()).hexdigest()!=WORKFLOW_SHA:fail('not exact successful 26954 executed historical workflow SHA')
 oldmark='      - name: Fetch only actually successful 26953 Actions artifact 14370867853 with proven authenticated curl'
 newmark='      # ALL 34 SUCCESSFUL 26954 historical preflight steps above are BYTE-EXACT'
 if old.count(oldmark)!=1 or new.count(newmark)!=1:fail('inherited exact 34-stage anchor missing')
 priorprefix=old.split(oldmark,1)[0]
 priorprefix=priorprefix.replace('Photon 26954 - Exact 26940 B OFF/Night SDR colors + single global +1EV, original highlight UHDR',
                              'Photon 26955 - Keep 26954 B OFF all-zoom and B Night SDR/UHDR, change only editor EV to +0.4')
 priorprefix=priorprefix.replace('      - TRIGGER_26954.txt\n','      - TRIGGER_26955.txt\n')
 if priorprefix!=new.split(newmark,1)[0]:fail('changed one of successful previous 26954 historical preflight steps')
 if new.count('TRIGGER_26955.txt')!=1 or 'TRIGGER_26954.txt' in new.split('jobs:',1)[0]:fail('new-only unique trigger incorrect')
 if new.count('runs-on: ubuntu-24.04')!=1 or new.count('timeout-minutes: 120')!=1:fail('changed pinned runner or timeout')
 if new.count('permissions:\n  contents: read\n  actions: read')!=1:fail('changed successful artifact permissions')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in new or re.search(r'(?m)^\s*[- ]*dev\s*$',new):fail('wrong branch/dev exposure')
 if new.count(':app:assembleDebug --stacktrace')!=1 or new.count('actions/upload-artifact@v4')!=1 or 'if-no-files-found: error' not in new:fail('real assembly/publish skipped')
 if new.count('compile_26904_shaders_v2.sh')!=1 or new.count('verify_26904_v3_cmake_handoff.py --handoff')!=1 or 'test_26903_v3_archive_receipt.py' not in new:fail('original 26886/26887,26903/26904 CMake/SPIR-V historical failures bypassed')
 if 'test_26952_halo.py --payload' not in new or 'test_26954_tone_math.py --payload' not in new:fail('historical color/halo/protected predecessor checks omitted')
 ordered=('build_26955_incremental.py seal','test_26955_workflow_refs.py --on-actions',
          'test_26955_source.py --payload','test_26955_tone_math.py --payload','test_26955_patches.py --payload',
          'build_26955_incremental.py fetch','build_26955_incremental.py prepare-base','test_26954_source.py --live',
          'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
          'bash compile_26954_shaders.sh','26955_HISTORICAL_SHADER_PROOF.txt',
          'build_26955_incremental.py install','verify_26906_native_cache.py preflight',
          'prepare_26955_native.py from-success','bash compile_26955_shaders.sh',
          'build_26955_incremental.py verify-compiled',':app:assembleDebug --stacktrace',
          'test_26955_native.py --cmake','test_26955_native.py --apk',
          'verify_26906_native_cache.py postflight','build_26955_incremental.py finalize','actions/upload-artifact@v4')
 pos=-1
 for needle in ordered:
  found=new.find(needle,pos+1)
  if found<0:fail('missing/stale/unordered current Actions executable '+needle)
  pos=found
 for stale in ('build_26954_incremental.py fetch','build_26954_incremental.py prepare-base','prepare_26954_native.py from-success',
               'photon_26954_outputs/26954_gradle_assemble.log','IrisCamera-0.9726954-26954-iris-rawr-debug.apk\n            photon_26954_outputs/',
               'build_26953_incremental.py fetch'):
  if stale in new:fail('stale version fetch/Android assemble or duplicate staged artifact '+stale)
 if f'Fetch only actually successful 26954 Actions artifact {ART_ID}' not in new:fail('stale old artifact ID in new workflow UI/stage')
 scripts=sorted(set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new)))
 expected=(R/'26955_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if scripts!=expected or len(expected)!=len(set(expected)):fail('missing/unused/stale executable inventory '+str(sorted(set(scripts)^set(expected))[:10]))
 if '--on-actions' in sys.argv:
  for item in expected:
   if not (R/item).is_file():fail('referenced actual workflow executable absent '+item)
 builder=(R/'build_26955_incremental.py').read_text()
 for datum in (BUILDER_SHA,WORKFLOW_SHA,TAR_SHA,ART_SHA,PRIOR_APK_SHA,COMMIT,str(RUN),str(ART_ID)):
  if datum not in builder:fail('actual successful 26954 authority not byte-sealed in builder')
 if 'NCHANGE=2' not in builder or 'NPROTECTED=2053' not in builder:fail('wrong protected source scope')
 fetch=builder.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
 if "'curl','--fail','--location','--retry','3','--silent','--show-error'" not in fetch or "'-H','Authorization: Bearer '+token" not in fetch:fail('successful authenticated curl downloader weakened')
 if subprocess.run(['bash','-n',str(R/'compile_26955_shaders.sh')],capture_output=True).returncode:fail('new real compiler shell syntax bad')
 if subprocess.run([sys.executable,'-S','-m','py_compile',str(R/'build_26955_incremental.py')],capture_output=True).returncode:fail('new builder Python syntax bad')
 compiler=(R/'compile_26955_shaders.sh').read_text()
 for token in ('"$COMPILER" -S frag','"$COMPILER" -G --auto-map-locations --auto-map-bindings',
               '"$COMPILER" -V --target-env vulkan1.1', 'spirv-val --target-env opengl4.5',
               'spirv-opt --target-env=opengl4.5 -O','spirv-opt --target-env=vulkan1.1 -O'):
  if token not in compiler:fail('real changed shader compilation/SPIR-V optimization missing '+token)
 if 'spirv-opt --target-env opengl4.5' in compiler:fail('26904 V2 old invalid spirv optimizer syntax')
 render=(R/'handoff_payload_26955/app/src/main/assets/shaders/motionv2/render.glsl').read_text()
 stripped=re.sub(r'/\*.*?\*/|//[^\n]*','',render,flags=re.S)
 if re.search(r'\bfloat\s+(?:flat|coherent|restrict)\b',stripped):fail('26904/26952 reserved name regression')
 print('PASS 26955 exact successful 26954 34-step historical prefix, 26904/SPIR-V/CMake and 26903 receipt, 2053 protected, all workflow actions resolvable, no stale/unused refs')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26955 WORKFLOW BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
