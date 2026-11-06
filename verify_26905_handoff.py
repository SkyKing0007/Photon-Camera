#!/usr/bin/env python3
"""Read-only seal, exact successful-26904 parent-workflow transform and Photon 26905 scoped handoff."""
from __future__ import annotations
from pathlib import Path
import hashlib,re,sys,subprocess

R=Path(__file__).resolve().parent
SRC=['app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
     'app/src/main/cpp/iris26864/bridge/Iris26888BOffHdrqCoordinator.cpp','app/version.properties']
PARENT='.github/workflows/build-26904-v3-change-aware.yml'
NEW='.github/workflows/build-26905-change-aware.yml'
PARENT_SHA='b5708d922589b54d8d00d0c3831e8d46000df06d962d1fdb413df3e9859b6485'
TRIGGER=b'RUN_26905_B_OFF_NORMAL_BURST_AND_NOISE_RECEIPT_V1\n'

def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def must(x,m):
    if not x:raise AssertionError('26905 handoff BLOCKED: '+m)
def transform(s):
    changes=[
      ('name: Photon 26904 V3 - independent change-aware Android build (Spektra pinned CMake compiler)',
       'name: Photon 26905 - Experiment B OFF full NORMAL burst and native noise fit receipt'),
      ('- TRIGGER_26904_V3.txt','- TRIGGER_26905.txt'),
      ('      - name: Verify 26904 V3 exact CMake compiler handoff and sealed scope',
       '''      - name: Prove 26905 exact staged scope and original 26904 compiled authority
        run: |
          python3 -S verify_26905_handoff.py
          python3 -S build_26905_incremental.py seal
          python3 -S test_26905_source.py . --with-javac
      - name: Verify 26904 V3 exact CMake compiler handoff and sealed scope'''),
      ('      - name: Obtain exact 26903 successful compiled-source authority',
       '      - name: Obtain exact 26904 successful compiled-source authority'),
      ('run: python3 -S build_26904_incremental.py fetch','run: python3 -S build_26905_incremental.py fetch'),
      ('      - name: Authority-seed exactly 2027 source files and apply six intended edits',
       '      - name: Authority-seed 2027 successful 26904 source files and apply three 26905 edits'),
      ('run: python3 -S build_26904_incremental.py prepare','run: python3 -S build_26905_incremental.py prepare'),
      ('      - name: Re-run actual candidate scope and ownership unit tests\n        run: python3 -S test_26904_changeaware.py . --with-javac --installed',
       '      - name: Re-run exact 26905 candidate byte and executable predicate checks\n        run: python3 -S test_26905_source.py . --with-javac --installed'),
      ('      - name: Freeze six-file affected scope after generated SPIR-V\n        run: python3 -S build_26904_incremental.py verify-compiled',
       '      - name: Freeze three-file affected scope with byte-identical pinned SPIR-V\n        run: python3 -S build_26905_incremental.py verify-compiled'),
      ('python3 -S build_26904_incremental.py finalize','python3 -S build_26905_incremental.py finalize'),
      ('tee photon_26904_incremental_outputs/26904_gradle_assemble.log',
       'tee photon_26905_incremental_outputs/26905_gradle_assemble.log'),
      ('      - name: Publish one successful 26904 release proof and APK',
       '      - name: Publish successful 26905 proof, exact builder/workflow, and APK'),
      ('name: photon-26904-changeaware-border-night-b-experimental',
       'name: photon-26905-b-off-all-normal-native-noise-receipt'),
      ('IrisCamera-0.9726904-26904-iris-rawr-debug.apk\n            photon_26904_incremental_outputs/',
       'IrisCamera-0.9726905-26905-iris-rawr-debug.apk\n            photon_26905_incremental_outputs/')]
    for a,b in changes:
        must(s.count(a)==1,'original workflow anchor cardinality '+a[:70])
        s=s.replace(a,b,1)
    return s

def check():
    paths=(R/'26905_STAGE1_PATHS.txt').read_text().splitlines()
    expected=['26905_HANDOFF_HASHES.sha256','26905_STAGE1_PATHS.txt','26905_BASE_26904_FULL_APP.sha256',
        '26905_PRECOMPILE_EXPECTED_FULL_APP.sha256','26905_CHANGED_RUNTIME_ALLOWLIST.txt',
        'build_26905_incremental.py','test_26905_source.py','verify_26905_handoff.py']+['handoff_payload_26905/'+x for x in SRC]
    must(paths==expected,'unexpected stage1 file list/order')
    must((R/'26905_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()==SRC,'source allowlist changed')
    must((R/'TRIGGER_26905.txt').read_bytes()==TRIGGER,'trigger exact bytes changed')
    entries={}
    for line in (R/'26905_HANDOFF_HASHES.sha256').read_text().splitlines():
        h,p=line.split('  ',1)
        must(p not in entries and re.fullmatch(r'[0-9a-f]{64}',h),'bad manifest row')
        entries[p]=h
    must(set(entries)==(set(paths)-{'26905_HANDOFF_HASHES.sha256'})|{NEW,'TRIGGER_26905.txt'},
         'manifest path set incorrect')
    for p,h in entries.items():
        must((R/p).is_file() and sh(R/p)==h,'tampered sealed file: '+p)
    original=R/PARENT
    must(original.is_file() and sh(original)==PARENT_SHA,'26904 V3 successful exact workflow bytes missing')
    must((R/NEW).read_text()==transform(original.read_text()),
         '26905 workflow not exact pinned 26904 V3 scoped transform')
    workflow=(R/NEW).read_text()
    must(workflow.count('TRIGGER_26905.txt')==1 and workflow.count(':app:assembleDebug')==1,
         'new trigger or full assemble cardinality wrong')
    must(workflow.index('compile_26904_shaders_v2.sh')<workflow.index('verify_26904_v3_cmake_handoff.py --handoff')<
         workflow.index('build_26905_incremental.py verify-compiled')<workflow.index(':app:assembleDebug'),
         'lost original proven pinned glslang CMake handoff')
    must(workflow.index('build_26905_incremental.py prepare')<workflow.index('Restore native CMake outputs'),
         'native cache must be keyed after authority source installation')
    must('photon_26905_incremental_outputs/' in workflow and 'actions/upload-artifact@v4' in workflow,
         'release proof publication missing')
    must(workflow.count('python3 -S build_26905_incremental.py')==5,'build stage CLI count wrong')
    b=(R/'build_26905_incremental.py').read_text()
    for m in ('RUN_ID = 42239513792','ART_ID = 13517085033',
          "ART_SHA = 'b33d381ea30459f83d05ab9ac780014ae5bf250ea85447b1e7445483fe22115b'",
          "TAR_SHA = 'c63ab18da57d63eeacecd424caa398d3c66c13b7c81c7ed0a92f6f4849221cec'",
          '2027','26905_PROTECTED_SOURCE.sha256','ACTUAL_EXECUTED_build_26905_incremental.py'):
        must(m in b,'builder authority/archive receipt missing: '+m)
    before={};after={}
    for f,target in (('26905_BASE_26904_FULL_APP.sha256',before),('26905_PRECOMPILE_EXPECTED_FULL_APP.sha256',after)):
        for line in (R/f).read_text().splitlines():
            h,p=line.split('  ',1)
            must(p not in target and re.fullmatch(r'[0-9a-f]{64}',h) and p.startswith('app/')
                 and '..' not in Path(p).parts,'invalid source manifest '+f)
            target[p]=h
    must(before.keys()==after.keys() and len(before)==2027,'26904 to 26905 source inventory changed')
    must({p for p in before if before[p]!=after[p]}==set(SRC),'source change escaped exact allowlist')
    for p in SRC:must(sh(R/'handoff_payload_26905'/p)==after[p],'changed source bytes mismatch')
    must(before['app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv']==
         '5853f1a0da12bab4b8c9489b6b298f3710f90fb6e51660204ed43f49963809f1',
         'pinned compiled native shader asset changed without source authorization')
    print('PASS successful 26904 parent workflow exact-byte 26905 transform; seal; 2027 files / 2024 protected; generated SPV invariance; single assemble and artifact archival')

if __name__=='__main__':
    try:check()
    except Exception as e:
        print('26905 HANDOFF FAIL',e,file=sys.stderr);sys.exit(1)
