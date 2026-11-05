#!/usr/bin/env python3
"""Sealed Photon 26903 one-trigger, three-stage, 2026->2027 source handoff gate.
Only Stage1 manifest + payload + exact generated-runner receipt are uploaded.
This executes against staged REAL files; no APK, source tree, or runner uploaded.
"""
from pathlib import Path
import hashlib,re,sys
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name):
 rows={}
 for line in (R/name).read_text().splitlines():
  sha,sep,path=line.partition('  ')
  assert sep and re.fullmatch('[0-9a-f]{64}',sha) and path not in rows,(name,line)
  rows[path]=sha
 return rows
def staged(path):
 x=R/path
 if x.is_file():return x
 p=R.parent/'STAGE_2_WORKFLOW'/path
 if p.is_file():return p
 return R.parent/'STAGE_3_UPLOAD_LAST'/path
old=manifest('26903_BASE_FULL_APP.sha256');new=manifest('26903_EXPECTED_CANDIDATE_FULL_APP.sha256')
pro=manifest('26903_UNCHANGED_PROTECTED.sha256')
mod=sorted(x for x in old.keys()&new.keys() if old[x]!=new[x]);add=sorted(new.keys()-old.keys());delete=sorted(old.keys()-new.keys())
allow=(R/'26903_CHANGED_ALLOWLIST.txt').read_text().splitlines()
assert len(old)==2026 and len(new)==2027 and len(pro)==2014
assert len(mod)==12 and len(add)==1 and not delete
assert allow==sorted(mod+add) and add==(R/'26903_ADDITIONS.txt').read_text().splitlines()
assert not (R/'26903_DELETIONS.txt').read_bytes()
assert set(pro)==set(old)-set(mod) and all(pro[k]==old[k]==new[k] for k in pro)
pay=R/'handoff_payload_26903'
assert {x.relative_to(pay).as_posix() for x in pay.rglob('*') if x.is_file()}=={x.removeprefix('app/') for x in allow}
assert all(H(pay/x.removeprefix('app/'))==new[x] for x in allow)
assert 'VERSION_BUILD=26903' in (pay/'version.properties').read_text()
assert (R/'26903_FORWARD_FULL_INDEX.patch').read_bytes().count(b'diff --git')==13
assert (R/'26903_ROLLBACK_FULL_INDEX.patch').read_bytes().count(b'diff --git')==13
wf=staged('.github/workflows/build-26903-iris-rawr.yml');assert wf.is_file()
s=wf.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26903.txt'\n"
steps=('Replay exact successful 26902 parent runner','Derive SHA-sealed 26903 successor guarded runner','Run inherited 17-stage 26903 build','Prove single intended 26903 APK','Seal exact EXECUTED 26903 runner','Upload authoritative 26903 proof and APK')
assert s.count('      - name: ')==6 and all(s.count('      - name: '+x)==1 for x in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
for ver in ('26900','26901','26902','26903'):
 assert s.count(f'python3 -S generate_{ver}_build.py .')==2,(ver,'original parent generator replay')
assert s.count('bash build_26903_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26903')==1
assert s.count('IrisCamera-0.9726903-26903-iris-rawr-debug.apk')==3
assert s.count('build_26903_iris_rawr_outputs/')>=2
assert 'RUNTIME_ARTIFACT_ID=' not in s and 'RUNTIME_TAR_SHA=' not in s
runner_sha=manifest('26903_GENERATED_BUILD_SHA256.txt')
assert set(runner_sha)=={'build_26903_iris_rawr.sh'} and s.count('--expected-sha256 '+runner_sha['build_26903_iris_rawr.sh'])==1
assert s.count('26899_V1')==0
# Actual generated runner present after GitHub's generator execution: check SHA and stages.
r=R/'build_26903_iris_rawr.sh'
if r.is_file():
 assert H(r)==runner_sha['build_26903_iris_rawr.sh']
 text=r.read_text(); stages=re.findall(r'(?m)^([a-z_]+)\(\)\{',text)
 names=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in stages if x in names)==names
 assert '$ARTDIR/build_26901_iris_rawr_outputs/' not in text
 assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in text
 assert '26902_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt' in text
 assert '26902_HISTORICAL_PATCH_PROOF.txt' in text
 assert '26903_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt' in text
 assert '26903_CURRENT_PATCH_PROOF.txt' in text
 assert len(re.findall(r'(?m)^\s*\./gradlew :app:assembleDebug --stacktrace',text))==1
assert staged('TRIGGER_26903.txt').read_bytes()==b'RUN_26903_B_NIGHT_NORMAL_RAWR_JIN_50MP_DNG_FIRST_V1\n'
if sys.argv[1:]==['--draft']:
 print('PASS 26903 draft 12 changed 1 new 2014 protected, 6-step workflow sole trigger');sys.exit(0)
assert not sys.argv[1:]
seal=manifest('26903_HANDOFF_HASHES.sha256')
assert all(staged(k).is_file() and H(staged(k))==v for k,v in seal.items())
allow_upload=(R/'26903_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert allow_upload==sorted(set(allow_upload))
assert set(allow_upload)==set(seal)|{'26903_HANDOFF_HASHES.sha256'}
paths=[(R/f'26903_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert all(p==sorted(set(p)) for p in paths)
assert not set(paths[0])&set(paths[1]+paths[2]) and not set(paths[1])&set(paths[2])
assert sorted(paths[0]+paths[1]+paths[2])==allow_upload
assert paths[1]==['.github/workflows/build-26903-iris-rawr.yml'] and paths[2]==['TRIGGER_26903.txt']
assert 'generate_26903_build.py' in paths[0] and 'verify_26903.py' in paths[0]
assert all('build_26903_iris_rawr.sh' not in p for p in allow_upload)
assert not any('__pycache__' in p or p.endswith('.pyc') for p in allow_upload)
assert not any(p.suffix=='.apk' for p in R.rglob('*') if p.is_file())
print('PASS 26903 SHA-sealed exact three-stage',len(paths[0]),'+1+1 files, 13 runtime allow, 2014 protected; 17-stage exact generated runner archived on Actions')
