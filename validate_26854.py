#!/usr/bin/env python3
from pathlib import Path
import hashlib,re,sys,textwrap
B,C=map(Path,sys.argv[1:3])
ALLOW={'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt','app/version.properties'}
def H(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def U(root): return {str(p.relative_to(root)):H(p) for p in (root/'app').rglob('*') if p.is_file()}
def template_map(text):
    out={}
    pat=re.compile(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)(?:\s*:\s*String)?(?:\s+by\s+lazy\s*\{)?\s*=??\s*"""',re.M)
    # First handle ordinary '= """' and lazy patterns via line scan.
    names=set(re.findall(r'^\s*(?:private\s+)?val\s+([A-Za-z_]\w*)[^\n]*?"""',text,re.M))
    for name in names:
        pats=[r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'(?:\s*:\s*String)?\s*=\s*"""',r'^\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*:\s*String\s+by\s+lazy\s*\{\s*\n\s*"""']
        m=next((re.search(p,text,re.M) for p in pats if re.search(p,text,re.M)),None)
        if not m: continue
        a=text.find('"""',m.start())+3; z=text.find('""".trimIndent()',a)
        if z>=0: out[name]=textwrap.dedent(text[a:z]).strip('\n')
    return out
def function(text,sig):
    a=text.index(sig); brace=text.index('{',a); depth=0; in_str=False; esc=False
    for i in range(brace,len(text)):
        ch=text[i]
        if in_str:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch=='"': in_str=False
            continue
        if ch=='"': in_str=True; continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return text[a:i+1]
    raise AssertionError(sig)
b,c=U(B),U(C)
assert len(b)==1786 and len(c)==1786,(len(b),len(c))
assert set(b)==set(c),'runtime file-universe mismatch'
assert {p for p in b if b[p]!=c[p]}==ALLOW,'changed runtime allowlist mismatch'
S='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
T='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt'
bs=(B/S).read_text();cs=(C/S).read_text();bt=template_map(bs);ct=template_map(cs)
assert set(bt)==set(ct),('shader template universe',set(bt)^set(ct))
assert {name for name in bt if bt[name]!=ct[name]}=={'normalCfaNoiseClean26853'},'unexpected shader change'
shader=ct['normalCfaNoiseClean26853']
for m in ('uPhaseSignal','uSharedSupport','uPhaseValidity','uTemporalStats26853',
          'uCfaNoiseShot26854','uCfaNoiseRead26854','nEff26854','sigma26854',
          'normalizedDifference','sameMaterial','oCleanPhaseSignal=mix(center,consensus,blend)*sumW'):
 assert m in shader,m
for x in ('uDngQuadHeadroom','whiteBalance','uJpegNeutralClamp','hue','globalEffectiveSupport',
          'relativeResidual','noiseGate','crossPhase','fallback'):
 assert x not in shader,('forbidden new CFA owner',x)
assert cs.count('IRIS_26854_NOISE_CALIBRATED_CFA_OWNER')==1
assert 'IRIS_26852_SINGLE_OWNER_TEMPORAL_CFA_ACCUMULATOR' in cs
assert 'IRIS_26853_MULTIFRAME_NATIVE_CFA_DENOISE_OWNER' in (B/T).read_text()
bt=(B/T).read_text();ct=(C/T).read_text()
assert bt.count('renderSabreNormalCfaNoiseClean26853(')==ct.count('renderSabreNormalCfaNoiseClean26853(')
assert ct.count('referenceShotNoise26854')==4 and ct.count('referenceReadNoise26854')==4
for x in ('canonicalChannelAtPhase(phase)','referenceCalibration.shotNoise[channel] / calculationWhiteBalance[channel]',
          'referenceCalibration.readNoise[channel] / (gain * gain)',
          'uniform4fv(program, "uCfaNoiseShot26854", referenceShotNoise26854)',
          'uniform4fv(program, "uCfaNoiseRead26854", referenceReadNoise26854)'):
 assert x in ct,x
for sig in ['private fun clearSabreNormalDngAccumulator(', 'private fun renderSabreNormalDngMerge(',
  'private fun resolveSabreNormalDngSupportStats(','private fun renderSabreNormalMasterShortFusion26651(',
  'private fun renderSabreShadowLongLumaAccumulate26833(',
  'private fun renderSabreShadowLongPostVgnLumaApply26833(',
  'private fun renderSabreDehomogenize(']:
 assert function(bt,sig)==function(ct,sig),sig
v=(C/'app/version.properties').read_text()
assert 'VERSION_NAME=0.9726854' in v and 'VERSION_BUILD=26854' in v
print('PASS 26854 semantic ownership: exact 3-file delta, retained 26852/26853 temporal and protected owners, phase-ordered sensor-neutral shot/read noise, no residual owner resurrection')
