#!/usr/bin/env python3
"""Exact 26989 protected runtime and independently pinned legacy native behavior."""
from pathlib import Path
import argparse, importlib.util, sys, subprocess, hashlib
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('builder',R/'build_26990_incremental.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('--payload',action='store_true');p.add_argument('--live',action='store_true');o=p.parse_args();assert o.payload!=o.live
changed,base,expected=b.scope();root=R if o.live else R/'handoff_payload_26990'
N='app/src/main/cpp/iris26985c_lkr2420/tools/lkr-lite/src/main/cpp/'
J='app/src/main/java/com/particlesdevs/photoncamera/'
K='app/src/main/java/com/hinnka/mycamera/processor/'
legacy=b.parse(R/'26990_LEGACY_NATIVE.sha256')
assert set(legacy)=={N+x for x in ('lkrl_adapter.cpp','lkrl_finish.cpp','lkrl_full.cpp','lkrl_jni.cpp','lkrl_solver.cpp','shaders/fin.comp')}
assert set(legacy)-{N+'shaders/fin.comp'}=={q for q in changed if '/cpp/' in q}
for q,h in legacy.items():assert expected[q]==h,q
for q in changed:assert b.sha(root/q)==expected[q],q
s=(root/(J+'settings/Iris26856ABSettings.java')).read_text();assert 'return preferences.contains(C_SESSION) ? Mode.AMAZE_26855 : Mode.BJZHOU_26972C;' in s
assert 'prefs.edit().putBoolean(C_SESSION,false).putString(key,mode.id).commit()' in s
assert 'if (preferences.getBoolean(C_SESSION,false)) return Mode.BJZHOU_26972C;' in s
assert 'if (preferences.contains(PREFIX + physical)) return resolvedStoredMode' in s
assert 'return ORIGINAL_26850;' in s and 'if ("AB".equals(id)) return AMAZE_26855;' in s
full=(root/(N+'lkrl_full.cpp')).read_text();assert full.count('S.hdr_white =')==1 and 'S.hdr_white = hdr ? hdr_clip : 1.0f;' in full
assert 'hl_ratio' not in full and 'hl_cells' not in full and 'bool hdr = false;' in full and 'if (!prm.exposure.empty())' in full
assert 'if (hdr) { sp.clip = hdr_clip; sp.exposure = erel; }' in full
jni=(root/(N+'lkrl_jni.cpp')).read_text();assert 'prm.exposure.swap(g_exposure);' in jni and 'g_exposure.clear();' in jni and 'if (!ex) return;' in jni
assert 'highlight: 2.3.94 all-channels rule; opposed inpaint off; bracket HDR preserved' in jni
assert 'IRIS26985C_LKRL_HL_REC' not in jni and 'IRIS26985C_LKRL_HL_OLD' not in jni
sol=(root/(N+'lkrl_solver.cpp')).read_text();assert 'fa.desat ? 2 : 0 /* donor legacy all-channels rule */' in sol and '0.0f /* no opposed inpaint */' in sol and 'run(7)' not in sol[sol.index('bool LiteSolver::finish('):]
assert 'false, 0 /* C: 2.3.94 highlight rule; no rim reconstruction */' in (root/(N+'lkrl_adapter.cpp')).read_text()
finish=(root/(N+'lkrl_finish.cpp')).read_text();assert 'const float lo = 0.92f * prm.clip, hi = prm.clip;' in finish and 'hl_ratio' not in finish and 'LKRL_HL_REC' not in finish and 'LKRL_HL_OLD' not in finish
if o.live:
 b.exact(root,'26990_EXPECTED_FULL_APP.sha256','26990 live exact scope')
 bridge=(root/(K+'GlesIris26983COnLkrBridge.java')).read_text();capture=(root/(J+'capture/CaptureController.java')).read_text()
 assert 'bracket.length!=0' in bridge and 'Iris26985CLkrNative.nativeSetExposures(null)' in bridge and 'final float[] iris26985CBracketEvs = new float[0]' in capture
 assert 'iris26593TotalTarget >= 2 && !iris26905BOffAllNormal && !iris26983COnAtPress' in capture
 assert 'IRIS_26989_C_ALL_RAW_READY' in capture and 'IRIS_26989_C_ZSL_ADMISSION' in capture
 assert 'Iris26989CRawMemory.copy' in (root/(K+'Iris26972CPhysicalRawSpool.kt')).read_text()
 assert b.sha(root/(N+'shaders/fin.comp'))==legacy[N+'shaders/fin.comp']
 shader=(root/(N+'shaders/fin.comp')).read_text();assert 'bool rec = pc.desat == 1 && pc.hrec != 0.0;' in shader and 'bool old = pc.desat == 2;' in shader and 'float lo = (old ? 0.92 : 0.85) * pc.clip' in shader
 assert 'float v = (old || rec) ? min(xd.x, min(xd.y, xd.z))' in shader and 'if (!old) m = m * m * (3.0 - 2.0 * m);' in shader and 'm * (L / wb[c] - x[c * HW + i])' in shader
 cleanup=list((root/'app/src/main/assets').rglob('con_26986_rawlens_cleanup.frag'));assert len(cleanup)==1
 assert 'smoothstep(vec3(0.70 * ws), vec3(0.99 * ws), cameraRgb)' in cleanup[0].read_text()
 if (R/'verify_26989_con_glsl.py').is_file():
  subprocess.run([sys.executable,'-S','verify_26989_con_glsl.py'],cwd=R,check=True)
  subprocess.run([sys.executable,'-S','verify_26989_preview_glsl.py','--audit'],cwd=R,check=True)
 elif b.os.getenv('GITHUB_ACTIONS')=='true':raise RuntimeError('missing actual reused shader verifiers')
print('PASS exact legacy source, no expanded white, unchanged HDR-OFF admission and C RAW memory, default C and explicit A/B contract')
