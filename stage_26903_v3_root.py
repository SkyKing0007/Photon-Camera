#!/usr/bin/env python3
"""V3 sealed real repository 26902->26903 V1->V2->V3 64-path audit.
Older V1/V2 source, triggers, receipts, workflows are IMMUTABLE and verified on
THEIR OWN runners. Exact SHA-sealed V3 only changes evidence plumbing/scope.
"""
import hashlib,re,sys
from pathlib import Path
R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
RUNNER='a5e9b4923325a13d3ab54fbfe233f3fca0d79b3a6f43ae194fa5edcb1ab67b44'
PARENT='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'
V2='8624b1617ba9156af7501667f95e63e69f5fdf6384cec30ed48ee50a9b828762'
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')

def paths(n):
 p=(R/n).read_text().splitlines()
 assert p==sorted(set(p)) and all(x and not x.startswith('/') and '..' not in Path(x).parts for x in p),n
 return p

def manifest(n):
 v={}
 for line in (R/n).read_text().splitlines():
  sha,sep,name=line.partition('  ')
  assert sep=='  ' and re.fullmatch(r'[a-f0-9]{64}',sha) and name not in v,('invalid checksum',n,line)
  v[name]=sha
 return v

assert sys.argv[1:] in ([],['--draft'],['--runner'])
assert (R/'TRIGGER_26903.txt').read_bytes()==b'RUN_26903_B_NIGHT_NORMAL_RAWR_JIN_50MP_DNG_FIRST_V1\n'
assert (R/'TRIGGER_26903_V2.txt').read_bytes()==b'RUN_26903_B_NIGHT_ARCHIVED_RECEIPT_RELOCATION_V2\n'
assert (R/'TRIGGER_26903_V3.txt').read_bytes()==b'RUN_26903_B_NIGHT_CORRECT_EXECUTED_RUNNER_RECEIPT_V3\n'
assert H(R/'build_26902_iris_rawr.sh')==PARENT,'successful exact 26902 archived runner changed'
assert manifest('26903_GENERATED_BUILD_SHA256.txt')=={'build_26903_iris_rawr.sh':'5d932336627107556a1df870802b2e32046467d599ab4648fb57b7f78dc117ad'}
assert manifest('26903_V2_GENERATED_BUILD_SHA256.txt')=={'build_26903_iris_rawr.sh':V2}
assert manifest('26903_V3_GENERATED_BUILD_SHA256.txt')=={'build_26903_iris_rawr.sh':RUNNER}
for name,cnt in [('26903_BASE_FULL_APP.sha256',2026),('26903_EXPECTED_CANDIDATE_FULL_APP.sha256',2027),('26903_UNCHANGED_PROTECTED.sha256',2014)]:
 assert len(manifest(name))==cnt,name
original=manifest('26903_HANDOFF_HASHES.sha256')
assert len(original)==33 and all((R/p).is_file() and H(R/p)==sha for p,sha in original.items()),'V1 original source/hash seal drifted'
v2original=manifest('26903_V2_HANDOFF_HASHES.sha256')
assert len(v2original)==14 and all((R/p).is_file() and H(R/p)==sha for p,sha in v2original.items()),'V2 original source/hash seal drifted'
v1=paths('26903_REPOSITORY_UPLOAD_ALLOWLIST.txt')
v2=paths('26903_V2_REPOSITORY_UPLOAD_ALLOWLIST.txt')
v3=paths('26903_V3_REPOSITORY_UPLOAD_ALLOWLIST.txt')
cum2=paths('26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt')
cum3=paths('26903_V3_CUMULATIVE_REPOSITORY_ALLOWLIST.txt')
assert list(map(len,[v1,v2,v3,cum2,cum3]))==[34,15,15,49,64]
assert not (set(v1)&set(v2) or set(v2)&set(v3) or set(v1)&set(v3))
assert cum2==sorted(v1+v2) and cum3==sorted(v1+v2+v3)
S=[paths(f'26903_V3_STAGE_{i}_UPLOAD_PATHS.txt') for i in (1,2,3)]
assert list(map(len,S))==[13,1,1]
assert sorted(S[0]+S[1]+S[2])==v3
assert S[1]==['.github/workflows/build-26903-v3-iris-rawr.yml']
assert S[2]==['TRIGGER_26903_V3.txt']
assert not any(p.startswith('handoff_payload_26903/') or p.startswith('app/') for p in v3),'V3 runtime source forbidden'
assert H(R/'photon_preserve_successful_runner.py')=='22b30661c7c438900a912ee8e223389ff32176edbc30742714e7d5ec3bd850dd','successful original archiver altered'
old=(R/'photon_preserve_successful_runner.py').read_text()
a="generated = safe_file(root / f'{version}_GENERATED_BUILD_SHA256.txt')"
b="generated = safe_file(root / f'{version}_V3_GENERATED_BUILD_SHA256.txt')"
assert old.count(a)==1 and (R/'photon_preserve_26903_v3_runner.py').read_text()==old.replace(a,b),'V3 archive copy changed more than one receipt lookup'
assert (R/'photon_preserve_26903_v3_runner.py').read_text().count(b)==1
wf=R/S[1][0];assert wf.is_file()
s=wf.read_text()
assert s.startswith('name: Build 26903 V3 Experiment B Night Exact Executed Runner Archival\n')
assert s.count("      - 'TRIGGER_26903_V3.txt'")==1
assert s.split('  push:\n',1)[1].split('  workflow_dispatch:',1)[0]=="    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26903_V3.txt'\n"
steps=('Replay exact successful 26902 parent runner','Derive SHA-sealed 26903 successor guarded runner','Run inherited 17-stage 26903 build','Prove single intended 26903 APK','Seal exact EXECUTED 26903 runner','Upload authoritative 26903 proof and APK')
assert s.count('      - name: ')==6
assert all(s.count('      - name: '+name)==1 for name in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
assert s.count('bash build_26903_iris_rawr.sh')==1
assert s.count('photon_preserve_26903_v3_runner.py 26903 --root . --expected-sha256 '+RUNNER)==1
assert s.count('photon_preserve_successful_runner.py 26903')==0
assert 'sha256sum -c 26903_V3_GENERATED_BUILD_SHA256.txt\n          python3 -S photon_preserve_26903_v3_runner.py' in s
assert s.count('python3 -S generate_26903_v3_build.py .')==2
assert s.count('python3 -S generate_26903_v2_build.py .')==3
assert 'IrisCamera-0.9726903-26903-iris-rawr-debug.apk' in s
assert s.count('26903_V3_HANDOFF_HASHES.sha256')==1
assert s.count('validate_26903_v2_frozen_stage.py')>=1
assert 'test -f build_26903_iris_rawr_outputs/exact_generated_runner/EXACT_EXECUTED_RUNNER.sha256' in s
assert 'sha256sum -c EXACT_EXECUTED_RUNNER.sha256' in s
assert 'upload-artifact@v4' in s and 'build_26903_iris_rawr_outputs/' in s
# Original triggered workflows are not modified and never trigger this V3.
assert H(R/'.github/workflows/build-26903-v2-iris-rawr.yml')==v2original['.github/workflows/build-26903-v2-iris-rawr.yml']
assert H(R/'.github/workflows/build-26903-iris-rawr.yml')==original['.github/workflows/build-26903-iris-rawr.yml']
if sys.argv[1:]!=['--draft']:
 seal=manifest('26903_V3_HANDOFF_HASHES.sha256')
 assert set(seal)==set(v3)-{'26903_V3_HANDOFF_HASHES.sha256'},'V3 seal path universe mismatch'
 assert all((R/p).is_file() and H(R/p)==digest for p,digest in seal.items()),'V3 payload SHA mismatch'
 if sys.argv[1:]==['--runner']:
  f=R/'build_26903_iris_rawr.sh';assert f.is_file() and H(f)==RUNNER,'V3 actual executed runner SHA mismatch'
  code=f.read_text();fn=tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',code) if x in STAGES)
  assert fn==STAGES
  assert '26903_V3_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff' in code
  assert '26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff' not in code
  assert code.count('python3 -S validate_26903_v2_frozen_stage.py')==3
  assert 'sha256sum -c 26903_V3_GENERATED_BUILD_SHA256.txt' in code
  assert 'sha256sum -c 26901_historical_candidate_app_source.tar.gz.sha256' not in code
  assert "git merge-base --is-ancestor 'a8c121fc4ee9f72ee82f0c5dafc6c1652493ffc8' HEAD" in code
  assert len(re.findall(r'(?m)^\s*\./gradlew :app:assembleDebug --stacktrace',code))==1
print('PASS 26903 V3 immutable originals V1+V2 SHA-sealed, STRICT 64 Git paths, 13+1+1 staged, 17 inherited compiler stages, real archiver V3 receipt')
