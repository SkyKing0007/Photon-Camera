#!/usr/bin/env python3
"""Exact staged 26904 V3: new build workflow, NOT the old 17-stage runner.

Preserves all previously uploaded 26904 V1+V2 bytes and six runtime edits.
Proof includes exact V2->V3 workflow transform and the real CMake source
compiler-discovery contract (extracted from the actual 26904 payload).
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import importlib.util
# A read-only verifier must not generate unexpected __pycache__ inside upload root.
sys.dont_write_bytecode=True

R=Path(__file__).resolve().parent
V2='.github/workflows/build-26904-v2-change-aware.yml'
V3='.github/workflows/build-26904-v3-change-aware.yml'
SHA_V2 = {
    'compile_26904_shaders_v2.sh':'31e331583520de7a9568c19a0e169120c22bf06ada4d1537c35ceb7657c6c0f2',
    'verify_26904_v2_safety.py':'1e88b28940823ff215ea6a45ddf7e4e542755531954b3d533d79d09d426c0442',
    '26904_V2_HANDOFF_HASHES.sha256':'10768db4a0970585726901fff4d691b0f11ffec6da70ef4de6c6849b3dbfc746',
    '26904_V2_STAGE1_PATHS.txt':'ea80366a5720d73d3244c85cc6ccccfa7a3fe8709886ed44cbb996f75f4b3406',
    V2:'c56fc055cf2a1327d6ebc3b894f09a27fcd94551404d904ffdd211c7fd4c016d',
    'TRIGGER_26904_V2.txt':'80287169a185380b9bee2149282a4dd56c441ee4a6c0e9dc1ac789aa81957110',
}
V3_PATHS=['26904_V3_HANDOFF_HASHES.sha256','26904_V3_STAGE1_PATHS.txt',
          'verify_26904_v3_cmake_handoff.py','verify_26904_v3_safety.py']
V3_TRIGGER=b'RUN_26904_V3_SPEKTRA_PINNED_GLSLANG_CMAKE_HANDOFF\n'


def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def need(ok,why):
    if not ok:raise AssertionError('26904 V3 BLOCKED: '+why)


def derive_workflow(old:str)->str:
    edits=[
     ('Photon 26904 V2 - independent change-aware Android build (SPIRV optimizer CLI)',
      'Photon 26904 V3 - independent change-aware Android build (Spektra pinned CMake compiler)'),
     ('      - TRIGGER_26904_V2.txt','      - TRIGGER_26904_V3.txt'),
     ('      - name: Verify corrected SPIR-V optimizer CLI and V2 package\n',
      '      - name: Verify 26904 V3 exact CMake compiler handoff and sealed scope\n'
      '        run: python3 -S verify_26904_v3_safety.py\n'
      '      - name: Verify corrected SPIR-V optimizer CLI and V2 package\n'),
     ('        run: bash compile_26904_shaders_v2.sh\n',
      '        run: bash compile_26904_shaders_v2.sh\n'
      '      - name: Hand off exact pinned glslang 16.5.0 to Android CMake\n'
      '        run: python3 -S verify_26904_v3_cmake_handoff.py --handoff\n')]
    for before,after in edits:
        need(old.count(before)==1,'V2 workflow anchor multiplicity changed: '+before[:65])
        old=old.replace(before,after,1)
    return old


def check():
    if os.getenv('GITHUB_REPOSITORY'):
        need(os.environ['GITHUB_REPOSITORY']=='SkyKing0007/Photon-Camera','wrong repo')
        need(os.environ.get('GITHUB_REF_NAME')=='experimental-clean-photon-rebuild','wrong branch')
    for name,digest in SHA_V2.items():
        p=R/name
        need(p.is_file() and sha(p)==digest,'original committed V2 file tampered: '+name)
    paths=(R/'26904_V3_STAGE1_PATHS.txt').read_text().splitlines()
    need(paths==V3_PATHS,'unexpected V3 Stage1 file scope')
    need((R/'TRIGGER_26904_V3.txt').read_bytes()==V3_TRIGGER,
         'V3 trigger exact bytes changed')
    seal={}
    for line in (R/'26904_V3_HANDOFF_HASHES.sha256').read_text().splitlines():
        h,filename=line.split('  ',1)
        need(filename not in seal and len(h)==64,'V3 SHA manifest malformed/duplicate')
        seal[filename]=h
    expect=(set(paths)-{'26904_V3_HANDOFF_HASHES.sha256'})|{V3,'TRIGGER_26904_V3.txt'}
    need(set(seal)==expect,'V3 manifest missing or unexpected paths')
    for path,digest in seal.items():
        f=R/path
        need(f.is_file() and sha(f)==digest,'sealed V3 file altered: '+path)
    v2=(R/V2).read_text()
    v3=(R/V3).read_text()
    need(v3==derive_workflow(v2),'V3 changed original V2 workflow beyond exact four edits')
    need(v3.count('      - TRIGGER_26904_V3.txt')==1
         and '      - TRIGGER_26904_V2.txt' not in v3
         and '      - TRIGGER_26904.txt' not in v3,
         'V3 mistakenly triggers earlier workflows')
    need(v3.index('run: bash compile_26904_shaders_v2.sh')
         < v3.index('run: python3 -S verify_26904_v3_cmake_handoff.py --handoff')
         < v3.index('run: python3 -S build_26904_incremental.py verify-compiled')
         < v3.index(':app:assembleDebug'),
         'compiler path handoff must run AFTER real shaders and BEFORE CMake/Gradle')
    need('run: python3 -S verify_26904_v2_safety.py' in v3,
         'V2 historical regression removed')
    need(v3.count(':app:assembleDebug')==1,'exactly one full APK assembly required')
    need('actions/upload-artifact@v4' in v3,'APK publication removed')
    need('17-stage' not in v3,'old runner inadvertently restored')
    spec=importlib.util.spec_from_file_location('photon26904v3cmake',R/'verify_26904_v3_cmake_handoff.py')
    need(spec is not None and spec.loader is not None,'V3 handoff helper not importable')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    candidate=R/'handoff_payload_26904/app/src/main/cpp/CMakeLists.txt'
    need(mod.validate_cmake_guard(candidate)=='34839fde356957cd306c2e84385ceda54995170e6b43a3393b1b9e07d4bbf10d',
         'frozen original 26904 CMake source hash/guard changed')
    subprocess.run([sys.executable,'-S',str(R/'verify_26904_v3_cmake_handoff.py'),'--self-test'],
                   cwd=R,check=True,stdout=subprocess.DEVNULL)
    print('PASS 26904 V3 exact 5-path trigger/workflow handoff seal, original V1/V2 unchanged, real CMake guard and environment handoff self-test')


def negatives():
    # All tests use independent physical copies of original staged source;
    # no current working-tree or GitHub mutation occurs.
    edits=[
      ('V3 trigger altered','TRIGGER_26904_V3.txt',lambda x:x+b'INVALID\n'),
      ('V3 compiled tool helper altered','verify_26904_v3_cmake_handoff.py',lambda x:x+b'#bad\n'),
      ('V3 workflow erroneously re-triggers V2',V3,lambda x:x.replace(b'TRIGGER_26904_V3.txt',b'TRIGGER_26904_V2.txt')),
      ('V3 workflow drops handoff',V3,lambda x:x.replace(b'run: python3 -S verify_26904_v3_cmake_handoff.py --handoff',b'run: true')),
      ('V2 compiler source changed','compile_26904_shaders_v2.sh',lambda x:x+b'#bad\n'),
      ('V2 trigger modified','TRIGGER_26904_V2.txt',lambda x:x+b'#bad\n'),
      ('CMake guard source modified','handoff_payload_26904/app/src/main/cpp/CMakeLists.txt',lambda x:x.replace(b'find_program(IRIS26681_GLSLANG',b'find_program(WRONG_NAME')),
      ('V3 checksum missing','26904_V3_HANDOFF_HASHES.sha256',lambda x:b''),
    ]
    import tempfile
    for label,path,modify in edits:
        with tempfile.TemporaryDirectory(prefix='photon26904v3bad_') as td:
            dest=Path(td)
            shutil.copytree(R,dest,dirs_exist_ok=True)
            p=dest/path;before=p.read_bytes();after=modify(before)
            need(after!=before,'bad negative fixture:'+label)
            p.write_bytes(after)
            run=subprocess.run([sys.executable,'-S',str(dest/'verify_26904_v3_safety.py'),'--check'],cwd=dest,capture_output=True,text=True,timeout=12)
            need(run.returncode!=0,'unblocked negative:'+label)
    # Resigned malicious new workflow cannot evade the deterministic-parent delta.
    with tempfile.TemporaryDirectory(prefix='photon26904v3resealed_') as td:
        dest=Path(td);shutil.copytree(R,dest,dirs_exist_ok=True)
        p=dest/V3;p.write_text(p.read_text().replace('      - TRIGGER_26904_V3.txt','      - TRIGGER_26904_V2.txt'))
        manifest=dest/'26904_V3_HANDOFF_HASHES.sha256'
        manifest.write_text(manifest.read_text().replace(seal_get(R,V3),sha(p)))
        run=subprocess.run([sys.executable,'-S',str(dest/'verify_26904_v3_safety.py'),'--check'],cwd=dest,capture_output=True,text=True,timeout=12)
        need(run.returncode!=0,'resigned hostile V3 workflow accepted')
    print('PASS 26904 V3 9 negative mutations including re-sealed alternate workflow rejected')


def seal_get(root,path):
    for line in (root/'26904_V3_HANDOFF_HASHES.sha256').read_text().splitlines():
        h,p=line.split('  ',1)
        if p==path:return h
    raise AssertionError('missing V3 workflow seal')

if __name__=='__main__':
    try:
        need(len(sys.argv)==1 or sys.argv==[sys.argv[0],'--check'] or sys.argv==[sys.argv[0],'--negative'],
             'unsupported CLI')
        check()
        if len(sys.argv)==2 and sys.argv[1]=='--negative':negatives()
    except Exception as e:
        print('26904 V3 FAIL:',e,file=sys.stderr)
        sys.exit(1)
