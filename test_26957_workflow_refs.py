#!/usr/bin/env python3
"""26957 fail-closed original 26956 V2 executed workflow, exact 36 historical stages and no unused references."""
import hashlib,re,subprocess,sys
from pathlib import Path
from build_26957_incremental import R,fail,WORKFLOW_SHA,BUILDER_SHA,TAR_SHA,ART_SHA,COMMIT,RUN,ART_ID,PRIOR_APK_SHA,NCHANGE,NPROTECTED

def main():
 old=(R/'26956_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 new=(R/'.github/workflows/build-26957-change-aware.yml').read_text()
 if hashlib.sha256(old.encode()).hexdigest()!=WORKFLOW_SHA:fail('26956 actual successful workflow SHA mismatched')
 for lineno,line in enumerate(new.splitlines(),1):
  match=re.match(r'^\s*(?:-\s+)?name:\s*(.+?)\s*$',line)
  if match:
   v=match.group(1).strip()
   if ': ' in v and not (v.startswith('"') and v.endswith('"')) and not (v.startswith("'") and v.endswith("'")):
    fail(f'unquoted : in YAML name at line {lineno}')
 predecessor='      - name: Fetch only actually successful 26955 Actions artifact 14389263287 with proven authenticated curl'
 current='      - name: Seal 26957 connected Rawr 56c1b932 and 44e4f092 B-only source, optional chroma and protected modes'
 if old.count(predecessor)!=1 or new.count(current)!=1:fail('actual successful 26956 historical prefix anchor missing')
 inherited=old.split(predecessor,1)[0]
 inherited=inherited.replace('Photon 26956 - Rawr HDR+ Quality B OFF Night matched motion noise gate',
                             'Photon 26957 - Rawr HDR+ Quality complete effective-frame and motion-energy integration',1)
 inherited=inherited.replace('TRIGGER_26956.txt','TRIGGER_26957.txt',1)
 if new.split(current,1)[0]!=inherited:fail('a prior successful 26956 historical stage was changed or dropped')
 if len(re.findall(r'^\s{6}- name:',new,re.M))!=57:fail('missing or redundant workflow step')
 if new.count('TRIGGER_26957.txt')!=1 or new.count('runs-on: ubuntu-24.04')!=1 or new.count('timeout-minutes: 120')!=1:fail('pinned original trigger/runner changed')
 if 'branches:\n      - experimental-clean-photon-rebuild' not in new or re.search(r'(?m)^\s*[- ]*dev\s*$',new):fail('dev branch exposure')
 if new.count(':app:assembleDebug --stacktrace')!=1 or new.count('actions/upload-artifact@v4')!=1 or 'if-no-files-found: error' not in new:fail('mandatory full Android compile or artifact publish bypassed')
 for x in ('compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff','test_26903_v3_archive_receipt.py',
           'test_26952_halo.py --payload','test_26955_tone_math.py --payload','test_26956_motion.py --payload'):
  if x not in new:fail('protected historical regression missing '+x)
 sequence=('build_26957_incremental.py seal','test_26957_workflow_refs.py --on-actions',
           'test_26957_sealed_negatives.py','test_26957_source.py --payload','test_26957_motion.py --payload',
           'test_26957_tone_math.py --payload','test_26957_patches.py --payload',
           'build_26957_incremental.py fetch','build_26957_incremental.py prepare-base',
           'test_26956_source.py --live','compile_26904_shaders_v2.sh','verify_26904_v3_cmake_handoff.py --handoff',
           'bash compile_26956_shaders.sh','26957_HISTORICAL_SHADER_PROOF.txt',
           'build_26957_incremental.py install','verify_26906_native_cache.py preflight',
           'prepare_26957_native.py from-success','bash compile_26957_shaders.sh',
           'build_26957_incremental.py verify-compiled',':app:assembleDebug --stacktrace',
           'test_26957_native.py --cmake','test_26957_native.py --apk',
           'verify_26906_native_cache.py postflight','build_26957_incremental.py finalize',
           'actions/upload-artifact@v4')
 idx=-1
 for p in sequence:
  found=new.find(p,idx+1)
  if found<0:fail('missing/stale/wrong order current Actions step '+p)
  idx=found
 if f'Fetch only actually successful 26956 Actions artifact {ART_ID}' not in new:fail('old artifact ID')
 if 'IrisCamera-0.9726957-26957-iris-rawr-debug.apk' not in new:fail('wrong APK name')
 scripts=sorted(set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',new)))
 expected=(R/'26957_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if scripts!=expected or len(scripts)!=len(set(scripts)):fail('stale/missing/unused expected executables '+str(sorted(set(scripts)^set(expected))[:10]))
 if '--on-actions' in sys.argv:
  for script in expected:
   if not (R/script).is_file():fail('actual executable reference not installed '+script)
 if new.count('name: photon-26957-rawr-hdrq-two-commits-effective-chroma-b-off-night')!=1:fail('artifact identity wrong')
 builder=(R/'build_26957_incremental.py').read_text()
 for v in (BUILDER_SHA,WORKFLOW_SHA,TAR_SHA,ART_SHA,PRIOR_APK_SHA,COMMIT,str(RUN),str(ART_ID),f'NCHANGE={NCHANGE}',f'NPROTECTED={NPROTECTED}'):
  if v not in builder:fail('builder historical provenance or counts incorrect '+v)
 fetch=builder.split('def fetch():',1)[1].split('def safe_tar(',1)[0]
 for s in ("'curl','--fail','--location','--retry','3','--silent','--show-error'","'-H','Authorization: Bearer '+token"):
  if s not in fetch:fail('authenticated artifact download weakened')
 if subprocess.run(['bash','-n',str(R/'compile_26957_shaders.sh')],capture_output=True).returncode:fail('shader compiler shell script syntax error')
 for path in ['build_26957_incremental.py','test_26957_source.py','test_26957_motion.py','test_26957_native.py','test_26957_patches.py','test_26957_sealed_negatives.py']:
  if subprocess.run([sys.executable,'-S','-m','py_compile',str(R/path)],capture_output=True).returncode:fail('Python syntax invalid '+path)
 compile=(R/'compile_26957_shaders.sh').read_text()
 for t in ('"$COMPILER" -S frag','"$COMPILER" -G --auto-map-locations --auto-map-bindings','"$COMPILER" -V --target-env vulkan1.1',
           'spirv-val --target-env opengl4.5','spirv-opt --target-env=opengl4.5 -O','spirv-opt --target-env=vulkan1.1 -O',
           'Iris26887BOffHdrqMismatchNorm.comp'):
  if t not in compile:fail('real shader compilation/spv compiler regression missing '+t)
 if 'spirv-opt --target-env opengl4.5' in compile:fail('26904 V2 broken SPIRV CLI syntax')
 m=(R/'handoff_payload_26957/app/src/main/cpp/iris26864/bridge/Iris26887BOffHdrqMismatchNorm.comp').read_text()
 stripped=re.sub(r'/\*.*?\*/|//[^\n]*','',m,flags=re.S)
 if re.search(r'\b(?:float|int|vec[234])\s+(?:coherent|flat|restrict|sample|buffer)\b',stripped):fail('reserved GLSL identifier')
 print('PASS 26957 original 26956-success historical prefix, 57 real steps, 26904/26903 regressions, all '+str(len(scripts))+' workflow executable refs, no stale/forbidden names')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26957 WORKFLOW BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
