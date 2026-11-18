#!/usr/bin/env python3
"""26958 exact successful 26957 historical prefix + new complete Actions compile graph."""
import hashlib,re,subprocess,sys
from build_26958_incremental import R,fail,WORKFLOW_SHA,BUILDER_SHA,TAR_SHA,ART_SHA,COMMIT,RUN,ART_ID,PRIOR_APK_SHA,NCHANGE,NPROTECTED

def main():
 prior=(R/'26957_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml').read_text()
 now=(R/'.github/workflows/build-26958-change-aware.yml').read_text()
 if hashlib.sha256(prior.encode()).hexdigest()!=WORKFLOW_SHA:fail('26957 actually executed workflow changed')
 anchor='      - name: Fetch only actually successful 26956 Actions artifact 14395370637 with proven authenticated curl'
 new_anchor='      - name: Fetch only actually successful 26957 Actions artifact 14398233829 with proven authenticated curl'
 custom='      - name: Seal 26958 exact latest successful 26957 source, Rawr noise fallback and 11-strength comparison'
 if prior.count(anchor)!=1 or now.count(new_anchor)!=1 or now.count(custom)!=1:fail('historical boundary missing')
 expect=prior.split(anchor,1)[0].replace('Photon 26957 - Rawr HDR+ Quality complete effective-frame and motion-energy integration','Photon 26958 - Rawr HDRQ verified burst noise and temporal neighbour parity',1).replace('TRIGGER_26957.txt','TRIGGER_26958.txt',1)
 if now.split(custom,1)[0]!=expect:fail('a successful 26957 historical stage modified or dropped')
 if len(re.findall(r'^      - name:',now,re.M))!=58:fail('expected 58 guarded steps')
 if now.count('TRIGGER_26958.txt')!=1 or now.count('runs-on: ubuntu-24.04')!=1 or now.count('timeout-minutes: 120')!=1:fail('runner/trigger mismatch')
 if 'experimental-clean-photon-rebuild' not in now or re.search(r'(?m)^\s*[- ]*dev\s*$',now):fail('dev branch exposure')
 if now.count(':app:assembleDebug --stacktrace')!=1 or now.count('actions/upload-artifact@v4')!=1 or 'if-no-files-found: error' not in now:fail('real compilation/publish missing')
 for line in now.splitlines():
  m=re.match(r'^\s*(?:-\s+)?name:\s*(.+?)\s*$',line)
  if m and ': ' in m[1] and not (m[1][0] in ("\"","'")):fail('YAML unquoted colon')
 needed=['test_26903_v3_archive_receipt.py',
  'test_26956_motion.py --payload','test_26957_motion.py --payload',
  'test_26958_source.py --payload','test_26958_motion.py --payload',
  'build_26958_incremental.py fetch','build_26958_incremental.py prepare-base',
  'test_26957_source.py --live','compile_26904_shaders_v2.sh',
  'verify_26904_v3_cmake_handoff.py --handoff','compile_26957_shaders.sh',
  'build_26958_incremental.py install','prepare_26958_native.py from-success',
  'compile_26958_shaders.sh','build_26958_incremental.py verify-compiled',
  ':app:assembleDebug --stacktrace','test_26958_native.py --cmake',
  'test_26958_native.py --apk','verify_26906_native_cache.py postflight',
  'build_26958_incremental.py finalize','actions/upload-artifact@v4']
 cursor=-1
 for item in needed:
  pos=now.find(item,cursor+1)
  if pos<0:fail('missing/stale/wrong-ordered guarded workflow stage '+item)
  cursor=pos
 scripts=sorted(set(re.findall(r'\b(?:python3\s+-S\s+|bash\s+|\./)([\w.-]+\.(?:py|sh))\b',now)))
 expected=(R/'26958_EXPECTED_ACTION_EXECUTABLES.txt').read_text().splitlines()
 if scripts!=expected:fail('missing/unused/malformed executable list '+str(sorted(set(scripts)^set(expected))))
 if '--on-actions' in sys.argv:
  for s in expected:
   if not (R/s).is_file():fail('missing live executable '+s)
 builder=(R/'build_26958_incremental.py').read_text()
 for s in (BUILDER_SHA,WORKFLOW_SHA,TAR_SHA,ART_SHA,PRIOR_APK_SHA,COMMIT,str(RUN),str(ART_ID),
           f'NCHANGE={NCHANGE}',f'NPROTECTED={NPROTECTED}'):
  if s not in builder:fail('wrong authority/source scope '+s)
 if 'curl' not in builder or 'Authorization: Bearer ' not in builder:fail('authenticated artifact retrieval removed')
 if subprocess.run(['bash','-n',str(R/'compile_26958_shaders.sh')],capture_output=True).returncode:
  fail('real pinned GLSL script syntax')
 for s in ('build_26958_incremental.py','prepare_26958_native.py','test_26958_source.py',
  'test_26958_motion.py','test_26958_native.py','test_26958_patches.py','test_26958_sealed_negatives.py'):
  if subprocess.run([sys.executable,'-S','-m','py_compile',str(R/s)],capture_output=True).returncode:fail('bad Python '+s)
 print(f'PASS 26958 exact successful 26957 historical prefix, 58 steps, {len(scripts)} current executable references, full pinned shader/NDK/Kotlin/Java/assemble, no stale/unused names')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26958 WORKFLOW BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
