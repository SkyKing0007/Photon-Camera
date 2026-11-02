#!/usr/bin/env python3
"""Single trigger and actual failed historical version-guard negative / corrected positive."""
from pathlib import Path
import sys,tempfile,subprocess,shutil,hashlib,re
R=Path(__file__).resolve().parent
workflow=R/'.github/workflows/build-26896-iris-rawr.yml'
if not workflow.is_file():workflow=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26896-iris-rawr.yml'
w=workflow.read_text();p=w.index('  push:\n');q=w.index('  workflow_dispatch:',p)
assert w[p:q]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26896.txt'\n"
for add in ["      - 'generate_26896_build.py'\n","      - '.github/workflows/build-26896-iris-rawr.yml'\n","      - '26896_HANDOFF_HASHES.sha256'\n","      - 'handoff_payload_26896/**'\n"]:
 tam=w[:q]+add+w[q:];assert tam.count("      - '")>1 and tam[p:tam.index('  workflow_dispatch:',p)]!=w[p:q]
s1=(R/'26896_STAGE_1_UPLOAD_PATHS.txt').read_text().splitlines();s2=(R/'26896_STAGE_2_UPLOAD_PATHS.txt').read_text().splitlines();s3=(R/'26896_STAGE_3_UPLOAD_PATHS.txt').read_text().splitlines()
assert s2==['.github/workflows/build-26896-iris-rawr.yml'] and s3==['TRIGGER_26896.txt']
assert not set(s1)&set(s2+s3)
assert set(s1)|set(s2)|set(s3)==set((R/'26896_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
assert sys.argv[1:] in ([],['--runner'])
if sys.argv[1:]==['--runner']:
 runner=(R/'build_26896_iris_rawr.sh').read_text()
 stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in re.findall(r'\n([a-z_]+)\(\)\{',runner) if x in stages)==stages
 assert runner.count('clean_extract_replay(){')==1
 p=runner.index('\nclean_extract_replay(){');body=runner[p:runner.index('\n}',p)]
 assert body.count("VERSION_BUILD=26895")==1 and body.count("VERSION_BUILD=26896")==1
 assert '26895_historical_candidate_app_source.tar.gz' in body and '26896_candidate_app_source.tar.gz' in body
 for owner,needle in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'"),('assemble','./gradlew :app:assembleDebug --stacktrace')]:
  a=runner.index('\n'+owner+'(){');b=runner.index('\n}',a);assert runner[a:b].count(needle)==1
 assert runner.count('python3 -S verify_26896.py patch "$BASE" "$CAND" 26896_FORWARD_FULL_INDEX.patch 26896_ROLLBACK_FULL_INDEX.patch')==2
 assert subprocess.run(['bash','-n',str(R/'build_26896_iris_rawr.sh')],capture_output=True).returncode==0
 with tempfile.TemporaryDirectory(prefix='26896_actual_version_') as d:
  td=Path(d);(td/'app').mkdir();shutil.copyfile(R/'handoff_payload_26896/version.properties',td/'app/version.properties')
  def run_version(version):
   cmd="grep -Fx 'VERSION_BUILD=%s' $1/app/version.properties >/dev/null" % version
   return subprocess.run(['bash','-c',cmd,'--',str(td)],capture_output=True,text=True).returncode
  assert run_version(26895)!=0 and run_version(26896)==0
 print('PASS 26896 actual 17-stage emitted runner, inherited compiler commands and precise version positive/negative')
print('PASS 26896 sole trigger stage3, zero premature path filters, four negative trigger tests, strict upload partitions')
