#!/usr/bin/env python3
"""Seal EXACT delta from FAILED 26903 V1 to corrected 26903 V2.
The original Night B 13 runtime-source payload files and ORIGINAL V1
build workflow/trigger/runner receipt MUST stay byte-identical to V1.
The final Git diff from successful 26902 is the union of original V1 + V2.
"""
from pathlib import Path
import hashlib
import re
import sys

R=Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
V1SHA='5d932336627107556a1df870802b2e32046467d599ab4648fb57b7f78dc117ad'
PARENT='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'

def manifest(name):
    result={}
    for line in (R/name).read_text().splitlines():
        sha,sep,rel=line.partition('  ')
        assert sep=='  ' and re.fullmatch('[0-9a-f]{64}',sha) and rel and rel not in result,(name,line)
        result[rel]=sha
    return result

def paths(name):
    a=(R/name).read_text().splitlines()
    assert a==sorted(set(a)),name
    return a

def stage_file(path):
    f=R/path
    if f.is_file():return f
    for folder in ('STAGE_2_WORKFLOW','STAGE_3_UPLOAD_LAST'):
        p=R.parent/folder/path
        if p.is_file():return p
    return f

assert (R/'TRIGGER_26903.txt').read_bytes()==b'RUN_26903_B_NIGHT_NORMAL_RAWR_JIN_50MP_DNG_FIRST_V1\n','immutable failed V1 trigger changed'
assert (R/'TRIGGER_26903_V2.txt').read_bytes()==b'RUN_26903_B_NIGHT_ARCHIVED_RECEIPT_RELOCATION_V2\n','new V2 trigger wrong'
assert H(R/'.github/workflows/build-26903-iris-rawr.yml')=='c1d22213b98533a2e19f601853a7e02f96befb1c40f2cbff585f0cec164d04f2','original V1 workflow was edited'
assert H(R/'generate_26903_build.py')=='0412a7f56e5d12f5447755a15262183038f55cdf7bfbd65857effd82cdd9d0a6','original V1 generator changed'
assert H(R/'build_26902_iris_rawr.sh')==PARENT,'actual successfully executed 26902 runner changed'
orig=manifest('26903_HANDOFF_HASHES.sha256')
assert len(orig)==33 and all((R/p).is_file() and H(R/p)==s for p,s in orig.items()),'original V1 complete 34-file sealed staging mutated'
base=manifest('26903_BASE_FULL_APP.sha256');final=manifest('26903_EXPECTED_CANDIDATE_FULL_APP.sha256');pro=manifest('26903_UNCHANGED_PROTECTED.sha256')
allow=paths('26903_CHANGED_ALLOWLIST.txt')
assert len(base)==2026 and len(final)==2027 and len(pro)==2014 and len(allow)==13
assert {p for p in set(base)&set(final) if base[p]!=final[p]}|set(final)-set(base)==set(allow)
assert all(base[p]==pro[p]==final[p] for p in pro)
for p in allow:
    f=R/'handoff_payload_26903'/p.removeprefix('app/')
    assert f.is_file() and H(f)==final[p],('original 26903 Night B source changed',p)
assert (R/'26903_GENERATED_BUILD_SHA256.txt').read_text()==V1SHA+'  build_26903_iris_rawr.sh\n','original V1 runner SHA receipt mutated'

v1=paths('26903_REPOSITORY_UPLOAD_ALLOWLIST.txt')
v2=paths('26903_V2_REPOSITORY_UPLOAD_ALLOWLIST.txt')
cumulative=paths('26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt')
assert len(v1)==34 and len(v2)==15 and len(cumulative)==49
assert not set(v1)&set(v2),'V2 overwrites original failed V1 file'
assert cumulative==sorted(v1+v2),'V2 changed full Git diff allowlist from successful 26902'
stages=[paths(f'26903_V2_STAGE_{n}_UPLOAD_PATHS.txt') for n in (1,2,3)]
assert list(map(len,stages))==[13,1,1]
assert sorted(stages[0]+stages[1]+stages[2])==v2
assert stages[1]==['.github/workflows/build-26903-v2-iris-rawr.yml']
assert stages[2]==['TRIGGER_26903_V2.txt']
assert 'generate_26903_v2_build.py' in stages[0]
assert 'verify_26903_v2_archive_receipt.py' in stages[0]
assert 'validate_26903_v1_frozen_stage.py' in stages[0]
assert 'test_26903_v2_sealed_negatives.py' in stages[0]
assert 'stage_26903_v2_root.py' in stages[0]
assert '26903_V2_HANDOFF_HASHES.sha256' in stages[0]
assert not any(p.startswith('handoff_payload_26903/') for p in v2)
assert not any('build_26903_iris_rawr.sh'==p for p in v2)
wf=stage_file(stages[1][0]);assert wf.is_file()
s=wf.read_text()
a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26903_V2.txt'\n"
assert "      - 'TRIGGER_26903.txt'" not in s
steps=('Replay exact successful 26902 parent runner','Derive SHA-sealed 26903 successor guarded runner','Run inherited 17-stage 26903 build','Prove single intended 26903 APK','Seal exact EXECUTED 26903 runner','Upload authoritative 26903 proof and APK')
assert s.count('      - name: ')==6
assert all(s.count('      - name: '+n)==1 for n in steps)
assert all(s.index('      - name: '+x)<s.index('      - name: '+y) for x,y in zip(steps,steps[1:]))
assert s.count('bash build_26903_iris_rawr.sh')==1
assert s.count('photon_preserve_successful_runner.py 26903')==1
assert '--expected-sha256 '+manifest('26903_V2_GENERATED_BUILD_SHA256.txt')['build_26903_iris_rawr.sh'] in s
assert s.count('python3 -S generate_26903_build.py .')>=3
assert s.count('python3 -S generate_26903_v2_build.py .')==2
assert 'IrisCamera-0.9726903-26903-iris-rawr-debug.apk' in s
assert '26903_V2_HANDOFF_HASHES.sha256' in s
if sys.argv[1:]==['--draft']:
    print('PASS V2 original V1 staged runtime/baseline unchanged, independent V2 trigger/6-step workflow and exact cumulative Git diff')
    sys.exit(0)
assert sys.argv[1:] in ([],['--runner'])
seal=manifest('26903_V2_HANDOFF_HASHES.sha256')
assert set(seal)==set(v2)-{'26903_V2_HANDOFF_HASHES.sha256'},'V2 seal wrong path universe'
assert all(stage_file(p).is_file() and H(stage_file(p))==digest for p,digest in seal.items()),'V2 staged SHA mismatch'
runner=R/'build_26903_iris_rawr.sh'
if sys.argv[1:]==['--runner']:
    assert runner.is_file() and H(runner)==manifest('26903_V2_GENERATED_BUILD_SHA256.txt')['build_26903_iris_rawr.sh'],'generated V2 runner SHA incorrect'
    t=runner.read_text()
    stages17=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
    assert tuple(z for z in re.findall(r'(?m)^([a-z_]+)\(\)\{',t) if z in stages17)==stages17
    assert 'sha256sum -c 26901_historical_candidate_app_source.tar.gz.sha256' not in t
    assert 'verify_26903_v2_archive_receipt.py "$T01" "$ARTDIR/build_26902_iris_rawr_outputs/26901_historical_candidate_app_source.tar.gz.sha256"' in t
    assert 'sha256sum -c "$ARTDIR/' not in t
    assert '$ARTDIR/build_26901_iris_rawr_outputs/' not in t
    assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in t
    assert '26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt' in t
    assert 'git merge-base --is-ancestor \'7619f129b14d8077811fb3b8b414bc97cdb6c449\'' in t
    assert len(re.findall(r'(?m)^\s*\./gradlew :app:assembleDebug --stacktrace',t))==1
print('PASS EXACT 26903 V2 13+1+1 infrastructure-only staged bytes, frozen original Night B source 13, 2014 protected, immutable failed trigger; 17-stage historical reference safe')
