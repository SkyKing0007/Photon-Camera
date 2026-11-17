#!/usr/bin/env python3
"""Guard actual successful 26953 33-step prefix, historical compiler, all references, runner and upload graph."""
import hashlib,re,subprocess,sys
from build_26954_incremental import R,fail,scope,WORKFLOW_SHA,BUILDER_SHA,TAR_SHA,ART_SHA,PRIOR_APK_SHA,COMMIT,RUN,ART_ID

def main():
 old=(R/'26953_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 wf=R/'.github/workflows/build-26954-change-aware.yml';new=wf.read_text()
 if hashlib.sha256(old.encode()).hexdigest()!=WORKFLOW_SHA:fail('successful original executed 26953 workflow SHA changed')
 oldmark='      - name: Fetch only successful 26952 Actions artifact 14363883957 with proven authenticated curl'
 newmark='      # All 33 predecessor historical steps above are BYTE-IDENTICAL'
 if old.count(oldmark)!=1 or new.count(newmark)!=1:fail('missing exact successful prefix stage anchors')
 previous=old.split(oldmark,1)[0].replace('name: Photon 26953 - 26940 no-halo B SDR with global UHDR-body brightness and Night/high zoom','name: Photon 26954 - Exact 26940 B OFF/Night SDR colors + single global +1EV, original highlight UHDR').replace('      - TRIGGER_26953.txt\n','      - TRIGGER_26954.txt\n')
 if previous!=new.split(newmark,1)[0]:fail('predecessor successful 33 historical preflight steps modified!')
 if new.count('TRIGGER_26954.txt')!=1 or 'TRIGGER_26953.txt' in new.split('jobs:',1)[0]:fail('new unique trigger wrong')
 if new.count('runs-on: ubuntu-24.04')!=1 or new.count('timeout-minutes: 120')!=1:fail('runner or timeout changed')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in new or re.search(r'(?m)^\s*[- ]*dev\s*$',new):fail('dev reference/branch altered')
 if new.count('permissions:\n  contents: read\n  actions: read')!=1:fail('Actions artifact read permissions changed')
 if new.count(':app:assembleDebug --stacktrace')!=1 or new.count('actions/upload-artifact@v4')!=1 or 'if-no-files-found: error' not in new:fail('real Gradle assembly / artifact publication bypassed')
 if 'actions/cache/restore@v4' not in new or 'verify_26906_native_cache.py preflight' not in new or 'verify_26906_native_cache.py postflight' not in new:fail('native/proven cache protection omitted')
 if new.count('compile_26904_shaders_v2.sh')!=1 or new.count('verify_26904_v3_cmake_handoff.py --handoff')!=1 or 'test_26903_v3_archive_receipt.py' not in new:fail('original 26886/26887/26903/26904 targeted regression missing')
 ordered=('build_26954_incremental.py seal','build_26954_incremental.py fetch','build_26954_incremental.py prepare-base',
          'test_26953_source.py --live','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
          'bash compile_26953_shaders.sh','26954_HISTORICAL_SHADER_PROOF.txt','build_26954_incremental.py install',
          'verify_26906_native_cache.py preflight','prepare_26954_native.py from-success',
          'bash compile_26954_shaders.sh','build_26954_incremental.py verify-compiled',
          ':app:assembleDebug --stacktrace','test_26954_native.py --cmake','test_26954_native.py --apk',
          'verify_26906_native_cache.py postflight','build_26954_incremental.py finalize','actions/upload-artifact@v4')
 pos=-1
 for command in ordered:
  idx=new.find(command,pos+1)
  if idx<0:fail('missing/stale/unordered actual Actions command '+command)
  pos=idx
 for command in ('python3 -S test_26954_source.py --payload','python3 -S test_26954_tone_math.py --payload','python3 -S test_26954_patches.py --payload','python3 -S test_26954_sealed_negatives.py',
                 'python3 -S test_26954_workflow_refs.py --on-actions','python3 -S test_26954_native.py --native','python3 -S test_26954_native.py --apk'):
  if command not in new:fail('workflow skipped current test '+command)
 for stale in ('build_26953_incremental.py fetch','build_26953_incremental.py prepare','IrisCamera-0.9726953-26953-iris-rawr-debug.apk\n            photon_26953_outputs/',
               'build_26952_incremental.py fetch','prepare_26953_native.py from-success','26953_gradle_assemble.log'):
  if stale in new:fail('stale old source or prior native assembly '+stale)
 exp=(R/'26954_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 pattern=r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b'
 scripts=sorted(set(re.findall(pattern,new)))
 if exp!=scripts or len(exp)!=len(set(exp)):fail('missing/stale/unused executable references '+str(sorted(set(exp)^set(scripts))[:10]))
 if '--on-actions' in sys.argv:
  for p in exp:
   if not (R/p).is_file():fail('actual historical Actions executable missing '+p)
 builder=(R/'build_26954_incremental.py').read_text()
 for code in (BUILDER_SHA,WORKFLOW_SHA,TAR_SHA,ART_SHA,PRIOR_APK_SHA,COMMIT,str(RUN),str(ART_ID)):
  if code not in builder:fail('actual predecessor successful authority not hard-sealed '+code)
 if 'NPROTECTED=2051' not in builder or 'NCHANGE=4' not in builder:fail('runtime source count wrong')
 fetch=builder.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
 if "'curl','--fail','--location','--retry','3','--silent','--show-error'" not in fetch or "'-H','Authorization: Bearer '+token" not in fetch:fail('original successful authenticated curl redirect downloader changed')
 if subprocess.run(['bash','-n',str(R/'compile_26954_shaders.sh')],capture_output=True).returncode:fail('actual mandatory compiler script bash syntax invalid')
 if subprocess.run([sys.executable,'-S','-m','py_compile',str(R/'build_26954_incremental.py')],capture_output=True).returncode:fail('actual build script syntax invalid')
 compile=(R/'compile_26954_shaders.sh').read_text()
 for token in ('"$COMPILER" -S frag', '"$COMPILER" -G --auto-map-locations --auto-map-bindings', '"$COMPILER" -V --target-env vulkan1.1','spirv-val --target-env opengl4.5','spirv-opt --target-env=opengl4.5 -O','spirv-opt --target-env=vulkan1.1 -O'):
  if token not in compile:fail('real glslang/SPIRV optimized shader step missing '+token)
 if 'spirv-opt --target-env opengl4.5' in compile:fail('26904 V2 wrong SPIR-V optimizer CLI')
 for src in ('render','gainmap'):
  data=(R/'handoff_payload_26954/app/src/main/assets/shaders/motionv2'/f'{src}.glsl').read_text()
  code=re.sub(r'/\*.*?\*/|//[^\n]*','',data,flags=re.S)
  if re.search(r'\bfloat\s+(?:flat|coherent|restrict)\b',code):fail('historical GLSL reserved token leak')
 print('PASS 26954 historical actual 26953 prefix, 26904+ real shader+SPIR-V+CMake, full NDK/Java/Kotlin/Gradle and 3-stage source graph no stale/unused/missing')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26954 WORKFLOW BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
