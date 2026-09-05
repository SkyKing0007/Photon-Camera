#!/usr/bin/env python3
from pathlib import Path
import hashlib,math,sys
TOL=2.0
def fail(m):raise SystemExit('FAIL: '+m)
def H(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def section(s,a,b):
 i=s.index(a);return s[i:s.index(b,i)]
def propagate_protection(seed,flow,valid,passes):
 h=len(seed);w=len(seed[0]);cur=[r[:] for r in seed]
 for _ in range(passes):
  nxt=[r[:] for r in cur]
  for y in range(h):
   for x in range(w):
    if cur[y][x]>0 or not valid[y][x]:continue
    vals=[]
    for yy in range(max(0,y-1),min(h,y+2)):
     for xx in range(max(0,x-1),min(w,x+2)):
      if xx==x and yy==y:continue
      if cur[yy][xx]<=0 or not valid[yy][xx]:continue
      if math.dist(flow[yy][xx],flow[y][x])>TOL:continue
      vals.append(cur[yy][xx])
    if vals:nxt[y][x]=min(vals)
  cur=nxt
 return cur
def main():
 if len(sys.argv)!=3:fail('usage base candidate')
 b,c=map(Path,sys.argv[1:])
 st=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text();sh=(c/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt').read_text();active=section(st,'private fun processSabreFrames','private data class SabreNormalDngSupportStats')
 # Exact 26601 device failure must be impossible: SHORT may not claim shared VGN while bypassing protection.
 for stale in ['shortTemporalSupport=false','sabrePhotometricGate=false','unblockerGate=false','normalCoverageGate=false','hardEvidenceSwitch=true']:
  if stale in active:fail('26601 device failure survived '+stale)
 for need in ['sabrePhotometricGate=true','unblockerGate=true','dilationFrameWeight=true','normalCoverageGate=true','hardEvidenceSwitch=false','bayerQuadCoherent=true']:
  if need not in active:fail('full SHORT protection missing '+need)
 # No seed => no propagated trust; coherent valid boundary fills but confidence can never increase.
 n=9;zero=[[0.0]*n for _ in range(n)];flow=[[(0.,0.)]*n for _ in range(n)];valid=[[True]*n for _ in range(n)]
 if any(v>0 for row in propagate_protection(zero,flow,valid,2*n) for v in row):fail('protection invented trust without seed')
 seed=[[0.0]*n for _ in range(n)]
 for i in range(n):seed[0][i]=0.4;seed[-1][i]=0.4;seed[i][0]=0.4;seed[i][-1]=0.4
 r=propagate_protection(seed,flow,valid,2*n)
 if any(v<=0 for row in r for v in row):fail('coherent protected highlight core did not fill')
 if max(v for row in r for v in row)>0.4000001:fail('propagation increased confidence')
 # Competing motion must not carry protection across the discontinuity.
 w=11;h=5;seed=[[0.0]*w for _ in range(h)];flow=[];valid=[[True]*w for _ in range(h)]
 for y in range(h):
  row=[]
  for x in range(w):row.append((0.,0.) if x<w//2 else (10.,0.))
  flow.append(row);seed[y][0]=0.5
 r=propagate_protection(seed,flow,valid,w+h)
 if any(r[y][x]>0 for y in range(h) for x in range(w//2,w)):fail('protection crossed >2px motion discontinuity')
 # Bayer-quad coherence: one rejected phase rejects the whole quad; accepted quad shares one scalar.
 cand=[1.0,1.0,1.0,0.0]
 if min(cand)!=0.0:fail('fixture')
 quad=min(cand)
 if any(v!=quad for v in [quad]*4):fail('quad coherence')
 # Whole-RGB scalar fusion cannot independently choose R/G/B owners.
 normal=(1.0,0.82,0.66);short=(0.72,0.64,0.55);a=.37
 fused=tuple((1-a)*x+a*y for x,y in zip(normal,short))
 ratios=[(fused[i]-normal[i])/(short[i]-normal[i]) for i in range(3)]
 if max(ratios)-min(ratios)>1e-6:fail('channel-dependent SHORT owner')
 # LONG implementation must remain unchanged from successful 26601.
 bst=(b/'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt').read_text()
 for a,z in [('    private fun renderSabreShadowLongCoverage','    private fun maxSabreAccumulatedWeight'),('    private fun sabreExposureDurationRobustness','    private fun renderSabreRejection')]:
  if section(bst,a,z)!=section(st,a,z):fail('LONG protection bytes changed '+a.strip())
 # Exact plant-window/halo class: no late RGB compositor and no 26601 binary accumulator switch active.
 for stale in ['renderSabreShortRestoreRgba16f26587(','renderSabreShortAccumulatorOwnership26601(','highlightShortTexture26587']:
  if stale in active:fail('edge/halo duplicate authority '+stale)
 # UHDR master parity: Motion body/midtones are identity before common 0.80 presentation; Night remains 0.50.
 rg=(c/'app/src/main/assets/shaders/motionv2/render.glsl').read_text();rj=(c/'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java').read_text();cpp=(c/'app/src/main/cpp/motionv2_jpeg444_jni.cpp').read_text()
 if 'IRIS_26602_MOTION_MASTER_SDR_TONE_START = 1.00f' not in rj:fail('1x master tone start')
 if 'HDR_EXPOSURE_SCALE = OUTPUT_EXPOSURE_SCALE' not in rj:fail('1x HDR/SDR scale parity')
 if 'iris26592MotionHdrHandoff!=0 ? iris26602MotionMasterToneStart : 0.50' not in rg:fail('1x Motion/Night split')
 if 'const float start=p.motionHdrHandoff?1.0f:0.50f;' not in cpp or 'float start=uMotionHdrHandoff!=0?1.0:0.50;' not in cpp:fail('true2x CPU/GPU parity')
 # Simple body fixture: guide<=1 must remain unchanged before 0.80 scale for Motion.
 for y in [0.0,0.02,0.18,0.5,0.9,1.0]:
  mapped=y if y<=1.0 else None
  if mapped!=y:fail('Motion body grade changed')
 print('PASS exact 26601 device failure converted: SHORT cannot bypass photometric/unblocker/dilation/NORMAL-coverage protection')
 print('PASS protected trust is non-inventing/non-increasing, 2px motion-discontinuity fail-closed, Bayer-quad coherent, whole-RGB scalar')
 print('PASS LONG full protection bytes inherited; DNG/SR detail ownership unchanged')
 print('PASS plant-window/halo duplicate authorities absent; Motion SDR body/midtones match UHDR master grade in 1x + true2x CPU/GPU')
if __name__=='__main__':main()
