#!/usr/bin/env python3
"""Exact C-only source, metadata/ownership boundary, and prior 2.4.20 byte recovery."""
import argparse,importlib.util,pathlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26989_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--payload',action='store_true');o=p.parse_args();assert o.live!=o.payload
changed,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26989'
if o.live:b.exact(root,'26989_EXPECTED_FULL_APP.sha256','26989 live exact scope')
else:
 for q in changed:assert b.sha(root/q)==expected[q],q
N='app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/'
K=root/'app/src/main/java/com/hinnka/mycamera/processor';J=root/'app/src/main/java/com/particlesdevs/photoncamera'
prior=b.parse(R/'26988_BASE_26987_FULL_APP.sha256') if (R/'26988_BASE_26987_FULL_APP.sha256').is_file() else None
# Historical manifest is already physically sealed by the inherited 26988 workflow. Require it live.
assert prior is not None
native={x for x in changed if '/cpp/' in x};assert native=={N+x for x in ('lkrl_adapter.cpp','lkrl_finish.cpp','lkrl_full.cpp','lkrl_jni.cpp','lkrl_solver.cpp')}
for q in native:assert b.sha(root/q)==prior[q],('not exact latest RawLens prior successful native byte',q)
for q in base:
 if q not in changed:assert expected[q]==base[q],q
s=(K/'Iris26972CPhysicalRawSpool.kt').read_text();session=(K/'Iris26972CCamera2ShutterSession.kt').read_text();m=(K/'Iris26989CRawMemory.kt').read_text();bridge=(K/'GlesIris26983COnLkrBridge.java').read_text();c=(J/'capture/CaptureController.java').read_text()
a=s.index('if (!shutter.night) {');z=s.index('// Preserve the separate C Night disk-backed route',a);motion=s[a:z]
assert 'Iris26989CRawMemory.copy' in motion and 'allocation::allocateNative, allocation::freeNative' in motion and 'return' in motion
assert not any(q in motion for q in ['File.createTempFile','MessageDigest','fd.sync','FileOutputStream','ByteArray('])
assert 'if (raw.memory != null) raw.memory.close()' in s and 'Iris26989CRawMemory.release(memoryReservation)' in s
assert 'return lease.readOnly()' in s and 'check(shutter.night)' in s and 'checkNotNull(raw.sha256).contentEquals' in s
assert 'image.close()' in s and 'if (shutter.night) 0L else diskLimitBytes' in s
assert 'private var sequenceReady = night' in session and 'if (!activated || !sequenceReady || state != State.COLLECTING) return' in session and '!active.hasCompletePhysicalBurst()) return' in session
assert session.index('!active.hasCompletePhysicalBurst()) return')<session.index('checkNotNull(readyListener).run()')<session.index('state = State.PROCESSING',session.index('checkNotNull(readyListener).run()'))
assert 'if (!night) owner.setReadyListener' in c and 'else owner.onSequenceReady()' in c and 'IRIS_26989_C_ALL_RAW_READY' in c
assert 'if (invalid) {' in c[c.index('private TotalCaptureResult iris26976CTrimOwnRingLocked'):c.index('/** C-owned AE->same-exposure RAW epoch')]
assert 'IRIS_26989_C_ZSL_ADMISSION' in c and 'total.getRequest() != mIris26975CProvenRawPreviewRequest' in c
assert 'normalExposure.longValue() != exposure.longValue()' in c and 'normalIso.intValue() != iso.intValue()' in c
assert 'final float[] iris26985CBracketEvs = new float[0]' in c and 'iris26593TotalTarget >= 2 && !iris26905BOffAllNormal && !iris26983COnAtPress' in c
assert 'bracket.length!=0' in bridge and 'Iris26985CLkrNative.nativeSetExposures(null)' in bridge and 'exposures[chosen]' in bridge
assert 'referenceKind=frozenNormalGroup actualLkrReferenceLoggedAtMerge=true' in c
assert 'mIris26988CPreview.beginManual(' in c and 'Iris26988CExposurePlan.plan(' in c
assert 'private var reserved = 0L' in m and 'owner = null' in m and 'asReadOnlyBuffer()' in m
if o.live:
 subprocess.run([sys.executable,'-S','verify_26989_con_glsl.py'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26989_preview_glsl.py','--audit'],cwd=R,check=True)
print('PASS exact C-only scope; latest 2.4.20 native bytes, zero HDR bracket admission, bounded memory, strict capture ownership and complete-burst animation')
