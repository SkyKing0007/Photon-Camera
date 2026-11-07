#!/usr/bin/env python3
"""Offline native cache replay regression with deliberately small patch fixtures.
No network, no compiler stubbing, no modifications to app/native/vendor source.
This only verifies the new CMake cache-state transition, not native compilation.
"""
from pathlib import Path
import tempfile, os, subprocess, sys, shutil

SCRIPT=Path(__file__).resolve().parent/'verify_26906_native_cache.py'
PATCH1=('diff --git a/CMakeLists.txt b/CMakeLists.txt\n'
        '--- a/CMakeLists.txt\n+++ b/CMakeLists.txt\n@@ -1 +1 @@\n-base\n+upstream\n')
PATCH2=('diff --git a/libheif/context.cc b/libheif/context.cc\n'
        '--- a/libheif/context.cc\n+++ b/libheif/context.cc\n@@ -1 +1 @@\n-original\n+aosp\n')

def cli(root,what,expect):
    p=subprocess.run([sys.executable,'-S',str(root/SCRIPT.name),what],cwd=root,
        env={**os.environ,'PHOTON_26906_NATIVE_CACHE_HIT':'true'},capture_output=True,text=True)
    if (p.returncode==0)!=expect:
        raise AssertionError(f'{what} expected success={expect}; returned={p.returncode}, stdout={p.stdout}, stderr={p.stderr}')

def fixture(root):
    shutil.copy2(SCRIPT,root/SCRIPT.name)
    p2=root/'app/src/main/cpp/iris26643_libheif_aosp_contract.patch'
    p2.parent.mkdir(parents=True,exist_ok=True);p2.write_text(PATCH2)
    result=[]
    for abi in ('arm64-v8a','armeabi-v7a'):
        base=root/'app/.cxx/Debug/exactfake'/abi
        src=base/'_deps/iris26636_libheif-src'
        (src/'libheif').mkdir(parents=True)
        (src/'CMakeLists.txt').write_text('base\n')
        (src/'libheif/context.cc').write_text('original\n')
        p1=base/'iris26636_libheif_pr1503.patch';p1.write_text(PATCH1)
        for patch in (p1,p2):subprocess.run(['git','apply',str(patch)],cwd=src,check=True)
        stamp=base/'_deps/iris26636_libheif-subbuild/iris26636_libheif-populate-prefix/src/iris26636_libheif-populate-stamp/iris26636_libheif-populate-patch'
        stamp.parent.mkdir(parents=True);stamp.write_text('stamped')
        result.append((src,p1,p2,stamp))
    return result

def run():
    with tempfile.TemporaryDirectory(prefix='photon-26906-native-replay-') as td:
        root=Path(td);records=fixture(root)
        cli(root,'preflight',True)
        for src,p1,p2,stamp in records:
            if (src/'CMakeLists.txt').read_text()!='base\n' or stamp.exists():
                raise AssertionError('cache was not restored to patchable state')
            for patch in (p1,p2):subprocess.run(['git','apply',str(patch)],cwd=src,check=True)
            stamp.write_text('real cmake fake for fixture only')
        cli(root,'postflight',True)
        # A native mutation after reapplying patches must fail final proof.
        (records[0][0]/'CMakeLists.txt').write_text('tampered\n')
        cli(root,'postflight',False)
    with tempfile.TemporaryDirectory(prefix='photon-26906-native-negative-') as td:
        root=Path(td);records=fixture(root)
        # An already damaged cache must never be accepted.
        (records[0][0]/'CMakeLists.txt').write_text('stale-upstream\n')
        cli(root,'preflight',False)
    with tempfile.TemporaryDirectory(prefix='photon-26906-native-cold-') as td:
        root=Path(td);shutil.copy2(SCRIPT,root/SCRIPT.name)
        env={**os.environ,'PHOTON_26906_NATIVE_CACHE_HIT':'false'}
        for name in ('preflight','postflight'):
            p=subprocess.run([sys.executable,'-S',str(root/SCRIPT.name),name],cwd=root,env=env,capture_output=True,text=True)
            if p.returncode:raise AssertionError('cold cache gate failed: '+p.stderr)
    print('PASS 26906 native patch replay both ABIs, exact content and stamp recovery; tampered caches reject; cold build proceeds')

if __name__=='__main__':run()
