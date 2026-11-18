#!/usr/bin/env python3
"""Fail-closed 26956 Actions graph, prior successful 26955 35-stage prefix, stale references and 26904 compiler regressions."""
import hashlib,re,sys,subprocess
from pathlib import Path
from build_26956_incremental import R,fail,WORKFLOW_SHA,BUILDER_SHA,TAR_SHA,ART_SHA,COMMIT,RUN,ART_ID,PRIOR_APK_SHA

def main():
 old=(R/'26955_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 new=(R/'.github/workflows/build-26956-change-aware.yml').read_text()
 # IRIS_26956_V2: GitHub rejects a workflow with an unquoted ': ' in a step name.
 # The V1 failure happened BEFORE job creation, so Actions could not execute our
 # existing on-runner static/reference checks. Scan all top-level and step names
 # for this exact YAML grammar hazard, without requiring PyYAML on the runner.
 for lineno,line in enumerate(new.splitlines(),1):
  m=re.match(r'^\s*(?:-\s+)?name:\s*(.+?)\s*$',line)
  if not m:continue
  value=m.group(1).strip()
  if ': ' in value and not (value.startswith('"') and value.endswith('"')) and not (value.startswith("'") and value.endswith("'")):
   fail(f'unquoted YAML colon in workflow name at line {lineno}; GitHub would reject before any build job starts')
 if new.count('      - name: "Install eight 26956 B HDRQ-only motion-gate source changes and version"')!=1:
  fail('26956 correctly quoted YAML install step missing')
 if hashlib.sha256(old.encode()).hexdigest()!=WORKFLOW_SHA:fail('not exact successful 26955 executed historical workflow SHA')
 oldmark='      - name: Fetch only actually successful 26954 Actions artifact 14382041542 with proven authenticated curl'
 newmark='      # Exact 35-step successful 26955 historical preflight prefix retained,'
 if old.count(oldmark)!=1 or new.count(newmark)!=1:fail('inherited exact 35-stage anchor missing')
 priorprefix=old.split(oldmark,1)[0]
 priorprefix=priorprefix.replace('Photon 26955 - Keep 26954 B OFF all-zoom and B Night SDR/UHDR, change only editor EV to +0.4',
                              'Photon 26956 - Rawr HDR+ Quality B OFF Night matched motion noise gate')
 priorprefix=priorprefix.replace('      - TRIGGER_26955.txt\n','      - TRIGGER_26956.txt\n')
 if priorprefix!=new.split(newmark,1)[0]:fail('changed one of successful previous 26955 historical preflight steps')
 if new.count('TRIGGER_26956.txt')!=1 or 'TRIGGER_26955.txt' in new.split('jobs:',1)[0]:fail('new-only unique trigger incorrect')
 if new.count('runs-on: ubuntu-24.04')!=1 or new.count('timeout-minutes: 120')!=1:fail('changed pinned runner or timeout')
 if new.count('permissions:\n  contents: read\n  actions: read')!=1:fail('changed successful artifact permissions')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in new or re.search(r'(?m)^\s*[- ]*dev\s*$',new):fail('wrong branch/dev exposure')
 if new.count(':app:assembleDebug --stacktrace')!=1 or new.count('actions/upload-artifact@v4')!=1 or 'if-no-files-found: error' not in new:fail('real assembly/publish skipped')
 if new.count('compile_26904_shaders_v2.sh')!=1 or new.count('verify_26904_v3_cmake_handoff.py --handoff')!=1 or 'test_26903_v3_archive_receipt.py' not in new:fail('original 26886/26887,26903/26904 CMake/SPIR-V historical failures bypassed')
 if 'test_26952_halo.py --payload' not in new or 'test_26955_tone_math.py --payload' not in new:fail('historical color/halo/protected predecessor checks omitted')
 ordered=('build_26956_incremental.py seal','test_26956_workflow_refs.py --on-actions',
          'test_26956_source.py --payload','test_26956_tone_math.py --payload','test_26956_patches.py --payload',
          'build_26956_incremental.py fetch','build_26956_incremental.py prepare-base','test_26955_source.py --live',
          'compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
          'bash compile_26955_shaders.sh','26956_HISTORICAL_SHADER_PROOF.txt',
          'build_26956_incremental.py install','verify_26906_native_cache.py preflight',
          'prepare_26956_native.py from-success','bash compile_26956_shaders.sh',
          'build_26956_incremental.py verify-compiled',':app:assembleDebug --stacktrace',
          'test_26956_native.py --cmake','test_26956_native.py --apk',
          'verify_26906_native_cache.py postflight','build_26956_incremental.py finalize','actions/upload-artifact@v4')
 pos=-1
 for needle in ordered:
  found=new.find(needle,pos+1)
  if found<0:fail('missing/stale/unordered current Actions executable '+needle)
  pos=found
 for stale in ('build_26955_incremental.py fetch','build_26955_incremental.py prepare-base','prepare_26955_native.py from-success',
               'photon_26955_outputs/26955_gradle_assemble.log','IrisCamera-0.9726955-26955-iris-rawr-debug.apk\n            photon_26955_outputs/',
               'build_26953_incremental.py fetch'):
  if stale in new:fail('stale version fetch/Android assemble or duplicate staged artifact '+stale)
 if f'Fetch only actually successful 26955 Actions artifact {ART_ID}' not in new:fail('stale old artifact ID in new workflow UI/stage')
 scripts=sorted(set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new)))
 expected=(R/'26956_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if scripts!=expected or len(expected)!=len(set(expected)):fail('missing/unused/stale executable inventory '+str(sorted(set(scripts)^set(expected))[:10]))
 if '--on-actions' in sys.argv:
  for item in expected:
   if not (R/item).is_file():fail('referenced actual workflow executable absent '+item)
 builder=(R/'build_26956_incremental.py').read_text()
 for datum in (BUILDER_SHA,WORKFLOW_SHA,TAR_SHA,ART_SHA,PRIOR_APK_SHA,COMMIT,str(RUN),str(ART_ID)):
  if datum not in builder:fail('actual successful 26955 authority not byte-sealed in builder')
 if 'NCHANGE=8' not in builder or 'NPROTECTED=2047' not in builder:fail('wrong protected source scope')
 fetch=builder.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
 if "'curl','--fail','--location','--retry','3','--silent','--show-error'" not in fetch or "'-H','Authorization: Bearer '+token" not in fetch:fail('successful authenticated curl downloader weakened')
 if subprocess.run(['bash','-n',str(R/'compile_26956_shaders.sh')],capture_output=True).returncode:fail('new real compiler shell syntax bad')
 if subprocess.run([sys.executable,'-S','-m','py_compile',str(R/'build_26956_incremental.py')],capture_output=True).returncode:fail('new builder Python syntax bad')
 compiler=(R/'compile_26956_shaders.sh').read_text()
 for token in ('"$COMPILER" -S frag','"$COMPILER" -G --auto-map-locations --auto-map-bindings',
               '"$COMPILER" -V --target-env vulkan1.1', 'spirv-val --target-env opengl4.5',
               'spirv-opt --target-env=opengl4.5 -O','spirv-opt --target-env=vulkan1.1 -O'):
  if token not in compiler:fail('real changed shader compilation/SPIR-V optimization missing '+token)
 if 'spirv-opt --target-env opengl4.5' in compiler:fail('26904 V2 old invalid spirv optimizer syntax')
 for path in ('Iris26887BOffHdrqMerge.comp','Iris26888BOffHdrqMismatch.comp'):
  shader=(R/'handoff_payload_26956/app/src/main/cpp/iris26864/bridge'/path).read_text()
  stripped=re.sub(r'/\*.*?\*/|//[^\n]*','',shader,flags=re.S)
  if re.search(r'\b(?:float|int|vec[234])\s+(?:flat|coherent|restrict)\b',stripped):fail('26904/26952 reserved name regression '+path)
 print('PASS 26956 exact successful 26955 34-step historical prefix, 26904/SPIR-V/CMake and 26903 receipt, 2047 protected, all workflow actions resolvable, no stale/unused refs')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26956 WORKFLOW BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
