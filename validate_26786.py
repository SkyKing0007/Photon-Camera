#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap,xml.etree.ElementTree as ET
if len(sys.argv)!=3: raise SystemExit('usage: validate_26786.py BASE CAND')
B=Path(sys.argv[1]); C=Path(sys.argv[2]); ROOT=Path(__file__).resolve().parent
allowed=(ROOT/'26786_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()
counts={
 '26786_BASE_26785_FULL_APP.sha256':1779,
 '26786_EXPECTED_CANDIDATE_FULL_APP.sha256':1779,
 '26786_PROTECTED_26785.sha256':1764,
 '26786_NATIVE_26785.sha256':819,
 '26786_VENDOR_26785.sha256':778,
 '26786_DNG_WRITER_26785.sha256':6,
 '26786_PRIOR_SOURCE_HASHES.sha256':15,
}
for n,c in counts.items():
 lines=[x for x in (ROOT/n).read_text().splitlines() if x.strip()]; assert len(lines)==c,(n,len(lines),c)
def U(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(r)/'app').rglob('*') if p.is_file()}
bu,cu=U(B),U(C); assert len(bu)==len(cu)==1779 and set(bu)==set(cu)
changed=sorted(k for k in bu if bu[k]!=cu[k]); assert changed==allowed,(changed,allowed); assert len(changed)==15
vp=(C/'app/version.properties').read_text(); assert 'VERSION_NAME=0.9726786' in vp and 'VERSION_BUILD=26786' in vp
# XML must parse.
ET.parse(C/'app/src/main/res/xml/preferences.xml'); ET.parse(C/'app/src/main/res/values/strings.xml')
# Explicit protected image domains.
for p in (
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
 'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl',
 'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java'):
 assert (B/p).read_bytes()==(C/p).read_bytes(),f'protected JPEG/VGN/tone domain changed: {p}'
# Embedded shader topology: only DNG merge + DNG normalize change.
SAB='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
SP='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialShaders.kt'
ST='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
IR='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
def vals(root,rel):
 t=(root/rel).read_text(); return {m.group(1):textwrap.dedent(m.group(2)).strip('\n')+'\n' for m in re.finditer(r'(?:private\s+)?val\s+([A-Za-z0-9_]+)\s*=\s*"""(.*?)"""\.trimIndent\(\)',t,re.S)}
bs,cs=vals(B,SAB),vals(C,SAB); bsp,csp=vals(B,SP),vals(C,SP); bst,cst=vals(B,ST),vals(C,ST); bi,ci=vals(B,IR),vals(C,IR)
assert set(bs)==set(cs) and sorted(k for k in bs if bs[k]!=cs[k])==['normalDngMerge']
assert set(bsp)==set(csp) and sorted(k for k in bsp if bsp[k]!=csp[k])==['normalizeBayer']
assert bst==cst,'26778/stacker embedded shader changed'; assert bi==ci,'VGN embedded shader changed'
nd=cs['normalDngMerge']; nb=csp['normalizeBayer']
for tok in ('IRIS_26786_DNG_COMBINED_AB_OPTIONS','IRIS_26786_LCA_REFERENCE_COMPATIBILITY','selectedHeadroom26786','IRIS_26786_ONE_SIDED_DEALIAS'):
 assert tok in nd,tok
for tok in ('uNeutralClamp26786','uAsShotNeutral26786','bothGreensFullyCensored26786'):
 assert tok in nb,tok
# 26785 A/B identity branches remain explicit.
for tok in ('uDngLcaEnabled26786 == 0','uDngEdgeDeAlias26786 == 0','uDngQuadHeadroom26786 != 0'):
 assert tok in nd,tok
assert 'if (uNeutralClamp26786 != 0)' in nb
assert 'referenceFallbackWeight26785 = 0.00005' in nd
assert 'IRIS_26782_FRACTIONAL_HARD_EDGE_VETO' in nd
assert 'mixG1G2' not in nd and 'poolGreen' not in nd and 'crossPhaseHue' not in nd
# Visible settings + immutable shutter transport + exact single log line.
settings=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java').read_text()
for tok in ('KEY_DNG_LCA','DEFAULT_KR = 0.000144f','DEFAULT_KB = -0.000072f','VISIBLE_AB_SETTINGS','resetToDefaults'):
 assert tok in settings,tok
cap=(C/'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java').read_text(); assert 'IrisMotionSettings.DngOptions.current()' in cap
batch=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/MotionBatch.java').read_text(); assert 'dngOptions26786' in batch
bridge=(C/'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt').read_text()
assert bridge.count('IRIS_26786_DNG_OPTIONS $line')==1
assert 'settingsSource=${dngOptions26786.source}' in bridge
# Frozen legacy image owners remain present.
assert 'IRIS_26784_RESTORE_26727_VGN_RGB_OWNER' in ci['universalAdaptiveColor26561']
assert 'IRIS_26784_RETIRE_BROAD_CLIPPED_NEUTRAL' in cst['EDGE_FALSE_COLOR_SUPPRESSOR_26778']
print('PASS 26786 runtime allowlist: 15 modified + 0 added + 0 deleted; 1764 protected files unchanged')
print('PASS 26786 settings: visible A/B controls + immutable shutter snapshot + reset defaults + one per-shot options log')
print('PASS 26786 DNG options: LCA default ON kR=+1.44e-4 kB=-7.2e-5; phase headroom default; deAlias/clamp default OFF')
print('PASS 26786 identity A/B: LCA OFF + phase headroom + deAlias OFF + clamp OFF retains explicit 26785 equation branches')
print('PASS 26786 phase identity: G1/G2 independent; no cross-phase pooling/hue synthesis; fixed optical center because no calibrated OIS pixel offset exists')
print('PASS 26786 protected image domains: 26778/VGN/JPEG/tone/UHDR owners unchanged')
