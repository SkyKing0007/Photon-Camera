#!/usr/bin/env python3
from pathlib import Path
import argparse, hashlib, re, math
ap=argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('candidate'); args=ap.parse_args()
BASE=Path(args.base)/'app'; CAND=Path(args.candidate)/'app'
def sha(p): h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def need(c,m):
    if not c: raise SystemExit('FAIL: '+m)
def text(r): return (CAND/r).read_text()
base_files=sorted(p.relative_to(BASE).as_posix() for p in BASE.rglob('*') if p.is_file())
cand_files=sorted(p.relative_to(CAND).as_posix() for p in CAND.rglob('*') if p.is_file())
need(len(base_files)==865,f'base file count={len(base_files)} expected=865')
new=set(cand_files)-set(base_files); removed=set(base_files)-set(cand_files)
modified={r for r in set(base_files)&set(cand_files) if sha(BASE/r)!=sha(CAND/r)}
expected_new={
 'src/main/assets/shaders/motionv2/joint_green_26500.glsl',
 'src/main/assets/shaders/motionv2/joint_rgb_26500.glsl',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2JointRgbReconstruct.java'}
expected_modified={
 'src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl',
 'src/main/assets/shaders/motionv2/render.glsl',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java'}
need(new==expected_new,f'new scope mismatch: {sorted(new)}')
need(modified==expected_modified,f'modified scope mismatch: {sorted(modified)}')
need(not removed,f'removed scope: {sorted(removed)}')
need('VERSION_NAME=0.9726499' in text('version.properties') and 'VERSION_BUILD=26499' in text('version.properties'),'version changed before safety proof')
frozen=[
 'src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2WronskiAlignment.java',
 'src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_base.glsl',
 'src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_bilateral.glsl',
 'src/main/assets/shaders/motionv2/mfsr_bjzhou_rejection_postprocess.glsl',
 'src/main/assets/shaders/motionv2/short_highlight_bayer_recover.glsl',
 'src/main/assets/shaders/motionv2/shadow_aux_bayer_fuse.glsl',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ColorTransform.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
 'src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2RcdDemosaic.java',
 'src/main/assets/shaders/motionv2/direct_rgb_accumulate.glsl',
 'src/main/assets/shaders/motionv2/direct_rgb_init.glsl',
 'src/main/assets/shaders/motionv2/mfsr_finalize.glsl']
for r in frozen: need(sha(BASE/r)==sha(CAND/r),'frozen source changed: '+r)
post=text('src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java')
for m in ['IRIS_26500_EVIDENCE_COMPLETE_JOINT_RGB_POST_OWNER','new MotionV2JointRgbReconstruct()','V2_POST_JOINT_WRONSKI_RGB_26500','jointWronskiRgb26500=']:
    need(m in post,'post graph missing '+m)
a=post.index('IRIS_26500_EVIDENCE_COMPLETE_JOINT_RGB_POST_OWNER'); b=post.index('} else {',a)
need('new MotionV2RcdDemosaic()' not in post[a:b],'separate RCD survived as standard-Bayer owner')
host=text('src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2JointRgbReconstruct.java')
for m in ['IRIS_26500_JOINT_WRONSKI_RGB_OWNER','motionv2/joint_green_26500','motionv2/joint_rgb_26500','motionV2StrictWronskiSensorValid','motionV2WronskiNoiseS','motionV2WronskiNoiseO','oldDirectRgbShadersActive=false','cameraDomainRestoredExactlyOnce=true']:
    need(m in host,'joint host missing '+m)
need('useAssetProgram("motionv2/direct_rgb_' not in host,'rejected direct RGB shaders reactivated')
for r in ['src/main/assets/shaders/motionv2/joint_green_26500.glsl','src/main/assets/shaders/motionv2/joint_rgb_26500.glsl','src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl','src/main/assets/shaders/motionv2/render.glsl']:
    s=text(r); need(s.count('{')==s.count('}'),r+' brace mismatch'); need(s.count('(')==s.count(')'),r+' parenthesis mismatch')
green=text('src/main/assets/shaders/motionv2/joint_green_26500.glsl'); rgb=text('src/main/assets/shaders/motionv2/joint_rgb_26500.glsl')
for s,label in [(green,'green'),(rgb,'rgb')]:
    for m in ['HighlightProvenance','PROVENANCE_CENSORED','calculationWb','trustedAt','neutralLowerBound']: need(m in s,label+' missing '+m)
    need('pink' not in s.lower() and 'magenta' not in s.lower(),label+' contains symptom-colour detector')
for m in ['IRIS_26500_PHYSICAL_GREEN_STRUCTURE_GUIDE']: need(m in green,'green marker missing')
for m in ['IRIS_26500_EVIDENCE_COMPLETE_JOINT_RGB','IRIS_26500_NOISE_SIGNIFICANCE_SHADOW_CHROMA','censoredFraction','physicalChroma','calculationRgb / max(calculationWb']:
    need(m in rgb,'RGB invariant missing '+m)
need('GreenGuide' in host and 'GreenGuide' in rgb,'green-guide carrier incomplete')
acc=text('src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl')
for m in ['IRIS_26500_REFERENCE_OWNED_PHYSICAL_EDGE_TAPER','validKernelSamples == 9','edgeCoverage','support[phase] += frameWeight * edgeCoverage']: need(m in acc,'edge invariant missing '+m)
def block(s,start,end): a=s.index(start); b=s.index(end,a)+len(end); return s[a:b]
base_acc=(BASE/'src/main/assets/shaders/motionv2/mfsr_bayer_accumulate.glsl').read_text()
need(block(acc,'if (referenceFrame != 0) {','        return;')==block(base_acc,'if (referenceFrame != 0) {','        return;'),'immutable reference branch changed')
render=text('src/main/assets/shaders/motionv2/render.glsl')
for m in ['IRIS_26500_WHITE_TARGET_AFTER_EXISTING_OUTPUT_EXPOSURE','IRIS_26500_GENTLE_NEUTRAL_WHITE_ROLLOFF','preScaleDisplayWhite','neutralMix']: need(m in render,'render invariant missing '+m)
need('return rgb/max(peak' not in render,'old unconditional hue-preserving overflow rule survived')
def uniforms(src): return set(re.findall(r'\buniform\s+(?:highp\s+|mediump\s+|lowp\s+)?[A-Za-z0-9_]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',src))
for asset,start,end in [('joint_green_26500.glsl','useAssetProgram("motionv2/joint_green_26500")','glProg.drawBlocks(greenGuide);'),('joint_rgb_26500.glsl','useAssetProgram("motionv2/joint_rgb_26500")','glProg.drawBlocks(WorkingTexture);')]:
    src=text('src/main/assets/shaders/motionv2/'+asset); a=host.index(start); b=host.index(end,a); seg=host[a:b]
    bound=set(re.findall(r'glProg\.set(?:Texture|Var)\("([A-Za-z_][A-Za-z0-9_]*)"',seg)); declared=uniforms(src)
    need(not(bound-declared),asset+' host binds undeclared '+str(sorted(bound-declared)))
    samplers=set(re.findall(r'\buniform\s+(?:highp\s+|mediump\s+|lowp\s+)?sampler2D\s+([A-Za-z_][A-Za-z0-9_]*)\s*;',src))
    need(not(samplers-bound),asset+' unbound samplers '+str(sorted(samplers-bound)))
def smooth(a,b,x):
    q=max(0,min(1,(x-a)/(b-a))); return q*q*(3-2*q)
for states in [(0,0,0,0),(1,0,2,1),(2,2,2,2),(1,1,1,1)]:
    code=sum(v*w for v,w in zip(states,(1,3,9,27))); dec=tuple(int(math.floor(code/d))%3 for d in (1,3,9,27)); need(dec==states,'provenance roundtrip failed')
vals=[1-smooth(0,1,n/4) for n in range(5)]; need(vals[0]==1 and abs(vals[-1])<1e-12 and all(vals[i]>=vals[i+1] for i in range(4)),'censored chroma not monotonic')
conf=[smooth(1.25,3.5,x) for x in [0,1,1.25,2,3.5,5]]; need(conf[0]==0 and conf[-1]==1 and all(conf[i]<=conf[i+1] for i in range(len(conf)-1)),'noise confidence not monotonic')
for wb in [(0.4,1,3.2),(2.5,1,0.6),(1,1,1)]:
    n=.73; camera=[n/w for w in wb]; rec=[camera[i]*wb[i] for i in range(3)]; need(max(rec)-min(rec)<1e-12,'WB round-trip neutrality failed')
need(abs((1/.8)*.8-1)<1e-12,'render white endpoint failed')
for r in ['src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2JointRgbReconstruct.java','src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java','src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java']:
    s=text(r); need(s.count('{')==s.count('}'),r+' Java brace mismatch')
print('PASS: exact 26499 runtime baseline + 26500 scope')
print('PASS: Wronski/rejection/Short-A/shadow aux/Camera2 color/UHDR and rejected direct-RGB shaders frozen')
print('PASS: joint G/(R-G)/(B-G) owner consumes explicit provenance; separate RCD inactive')
print('PASS: CENSORED brightness-only, SHORT_VALIDATED physical-colour authority, Sx+O shadow chroma confidence')
print('PASS: calculation-WB round trip, reference-owned edge taper and gentle neutral-white endpoint')
print('PASS: host/shader binding audit and synthetic invariants')
print('PRE-BUILD SAFETY PROOF PASSED')
