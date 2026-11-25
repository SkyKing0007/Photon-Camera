#!/usr/bin/env python3
import argparse,importlib.util,pathlib,subprocess,sys,re
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26985_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');o=p.parse_args();assert o.live!=o.payload
changed,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26985'
if o.live:b.exact(root,'26985_EXPECTED_FULL_APP.sha256','26985 live exact scope')
else:
 for q in changed:assert b.sha(root/q)==expected[q],q
k=root/'app/src/main/java/com/hinnka/mycamera/processor';j=root/'app/src/main/java/com/particlesdevs/photoncamera';cpp=root/'app/src/main/cpp'
bridge=(k/'GlesIris26983COnLkrBridge.java').read_text();p=(k/'GlesIris26983COnPipeline.kt').read_text();output=(k/'Iris26985CLinearOutput.kt').read_text();pub=(j/'processing/processor/Iris26983COnBatchPublication.java').read_text();jni=(k/'Iris26985CLkrNative.java').read_text()
assert bridge.count('Iris26985CLkrNative.nativeMerge(')==1 and 'Iris26985CLkrNative.nativeSetExposures(hdrExposures)' in bridge
assert bridge.index('output.consume(reconstructed')<bridge.index('nativePublishRgba16f(reconstructed') and 'Iris26985CLkrNative.nativeFree(reconstructed)' in bridge
assert 'rawSaver>=1?' in pub and 'rawSaver!=2?' in pub and 'PhotonMotionMgc1271Bridge' not in pub
assert 'GlesIris26983COnLkrBridge.run' in p and 'return linearOutput.dngSaved' in p
assert 'check(!consumed);consumed=true' in output and 'LinearRgbDngWriter.writeStriped' in output and 'LkrLensShading.applyShadingMapped' in output
assert 'System.loadLibrary("iris26985clkr2420")' in jni
assert 'add_library(iris26985clkr2420 SHARED' in (cpp/'iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/CMakeLists.txt').read_text()
assert 'iris26985c_lkr2420' in (cpp/'CMakeLists.txt').read_text()
assert 'IRIS26985C_NO_NNAPI=1' in (cpp/'iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/CMakeLists.txt').read_text()
assert all(not x.startswith('app/src/main/jniLibs/') for x in changed)
if o.live:
 subprocess.run([sys.executable,'-S',str(R/'verify_26985_con_glsl.py')],check=True)
else:subprocess.run([sys.executable,'-S',str(R/'verify_26985_native_glsl.py'),'--root',str(root),'--audit'],check=True)
print('PASS C-private library, one reconstruction, DNG-before-JPEG, exact 2474 protected files and output admission source contracts')
