#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26727_regressions.py BASE26726 CAND26727')
b=Path(sys.argv[1]); c=Path(sys.argv[2])
def txt(r,p): return (r/p).read_text()
def section(s,a,z):
 i=s.index(a); j=s.index(z,i+len(a)); return s[i:j]
# Exact 26727 scope is transport upload type only.
changed={
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java',
'app/version.properties'}
# Global FLOAT_16 semantics remain inherited: do not break older float32 client callers.
glf=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java')
bglf=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLFormat.java')
assert glf==bglf
assert 'case FLOAT_16:' in glf and 'return GL_FLOAT;' in glf
# New explicit half-client path is fail closed and never changes generic loadData.
glt=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java')
bglt=txt(b,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/GLTexture.java')
assert 'IRIS_26727_EXPLICIT_RGBA16F_CLIENT_UPLOAD' in glt
m=section(glt,'    public void loadHalfFloatData(ByteBuffer pixels) {','    void reSetParameters(){')
for t in ['GLFormat.DataType.FLOAT_16','* 2L','GL_HALF_FLOAT','glTexSubImage2D','previousBinding','26727 glTexSubImage2D GL_HALF_FLOAT']:
 assert t in m,t
assert 'mFormat.getGLType()' not in m
# Inherited generic upload stays byte-identical.
def method(s,a,z): return section(s,a,z)
assert method(glt,'    public void loadData(Buffer pixels){','    /* IRIS_26727_EXPLICIT_RGBA16F_CLIENT_UPLOAD').rstrip() == \
       method(bglt,'    public void loadData(Buffer pixels){','    void reSetParameters(){').rstrip()
# Motion: 8-Bpp direct carrier gets null-storage creation then explicit half upload.
mot=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2CfaInput.java')
assert 'IRIS_26727_MOTION_EXPLICIT_HALF_FLOAT_UPLOAD' in mot
route=section(mot,'            if (directRgbCarrier) {','        } finally {')
for t in ['GLFormat.DataType.FLOAT_16','null,','WorkingTexture.loadHalfFloatData(view)','GLFormat.DataType.FLOAT_32','view,']:
 assert t in route,t
assert 'new GLFormat(GLFormat.DataType.FLOAT_16, 4),\n                        view,' not in route
# Existing 26726 contract remains exact: 8-Bpp and RGBA16F ownership.
for t in ['4L * 2L','LINEAR_RGB_CARRIER_RGBA16F','source.capacity() != directHalfBytes']:
 assert t in mot,t
# Night: same explicit half upload and exact 8-Bpp contract.
night=txt(c,'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisNightRgbInput.java')
for t in ['IRIS_26727_NIGHT_EXPLICIT_HALF_FLOAT_UPLOAD','GLFormat.DataType.FLOAT_16','WorkingTexture.loadHalfFloatData(view)','4L * 2L','LINEAR_RGB_CARRIER_RGBA16F']:
 assert t in night,t
assert 'new GLFormat(GLFormat.DataType.FLOAT_16, 4),\n                view,' not in night
# Upstream carrier production and IQ owners must remain byte-identical.
protected=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java']
for p in protected:
 assert (b/p).read_bytes()==(c/p).read_bytes(),p
# Version exact.
v=txt(c,'app/version.properties')
assert 'VERSION_NAME=0.9726727' in v and 'VERSION_BUILD=26727' in v
print('PASS 26727 regressions: universal RGBA16F ownership preserved; 8-Bpp Motion/Night client bytes upload only as GL_HALF_FLOAT; inherited generic FLOAT16<-FLOAT32 conversion behavior unchanged; upstream carrier/IQ/capture owners byte-identical')

# Persisted manifest invariance proof.
def loadm(n):
 d={}
 for l in (Path(__file__).resolve().parent/n).read_text().splitlines():
  if l.strip(): h,p=l.split(None,1); d[p.strip()]=h
 return d
for stem,count in [('NATIVE_FULL',820),('VENDOR_PROTECTED',1),('DNG',6)]:
 x=loadm(f'26727_{stem}_BASE.sha256'); y=loadm(f'26727_{stem}_CANDIDATE.sha256'); assert len(x)==len(y)==count and x==y
