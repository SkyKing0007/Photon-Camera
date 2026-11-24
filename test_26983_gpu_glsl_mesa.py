import ctypes as c,os
os.environ['EGL_PLATFORM']='surfaceless';os.environ['LIBGL_ALWAYS_SOFTWARE']='1'
e=c.CDLL('libEGL.so.1');P=c.c_void_p;I=c.c_int;U=c.c_uint
for name,res,args in [('eglGetDisplay',P,[P]),('eglInitialize',U,[P,c.POINTER(I),c.POINTER(I)]),('eglBindAPI',U,[U]),('eglChooseConfig',U,[P,c.POINTER(I),c.POINTER(P),I,c.POINTER(I)]),('eglCreateContext',P,[P,P,P,c.POINTER(I)]),('eglMakeCurrent',U,[P,P,P,P]),('eglGetProcAddress',P,[c.c_char_p]),('eglGetError',U,[])]:
 f=getattr(e,name);f.restype=res;f.argtypes=args
D=e.eglGetDisplay(None);ma=I();mi=I();assert e.eglInitialize(D,c.byref(ma),c.byref(mi)),hex(e.eglGetError());print(ma.value,mi.value)
assert e.eglBindAPI(0x30A0);cf=P();n=I();at=(I*5)(0x3040,0x40,0x3033,1,0x3038);assert e.eglChooseConfig(D,at,c.byref(cf),1,c.byref(n)) and n.value
ct=e.eglCreateContext(D,cf,None,(I*3)(0x3098,3,0x3038));assert ct,hex(e.eglGetError());assert e.eglMakeCurrent(D,None,None,ct),hex(e.eglGetError())
def gl(n,r,*a):return c.CFUNCTYPE(r,*a)(e.eglGetProcAddress(n.encode()))
print(gl('glGetString',c.c_char_p,U)(0x1F02))
from pathlib import Path
import re,textwrap,json,hashlib
r=Path(__file__).resolve().parent; base=r/'actual/app/src/main'; cand=r/'candidate/app/src/main'; k='java/com/hinnka/mycamera/processor/'
def literal(p,n):
 s=p.read_text();m=re.search(r'\bval '+re.escape(n)+r'\s*=\s*"""(.*?)"""\.trimIndent\(\)',s,re.S);assert m,(p,n)
 # Kotlin trimIndent discards blank first/last lines; common indentation over all nonblank lines.
 return textwrap.dedent(m[1]).strip('\n')
create=gl('glCreateShader',U,U);source=gl('glShaderSource',None,U,I,c.POINTER(c.c_char_p),c.POINTER(I));compile=gl('glCompileShader',None,U);status=gl('glGetShaderiv',None,U,U,c.POINTER(I));log=gl('glGetShaderInfoLog',None,U,I,c.POINTER(I),c.c_char_p)
createp=gl('glCreateProgram',U);attach=gl('glAttachShader',None,U,U);link=gl('glLinkProgram',None,U);pstatus=gl('glGetProgramiv',None,U,U,c.POINTER(I));plog=gl('glGetProgramInfoLog',None,U,I,c.POINTER(I),c.c_char_p);dele=gl('glDeleteShader',None,U);delp=gl('glDeleteProgram',None,U)
def shader(text,kind,name):
 h=create(kind);assert h;raw=text.encode();src=c.c_char_p(raw);length=I(len(raw));source(h,1,c.byref(src),c.byref(length));compile(h);ok=I();status(h,0x8B81,c.byref(ok));msg=c.create_string_buffer(16000);log(h,len(msg),None,msg);assert ok.value,(name,msg.value.decode());return h
# Real software GLES compiler, independent of predecessor glslang/SPIR-V gate.
def program(parts,name):
 handles=[shader(src,typ,name) for typ,src in parts];p=createp();assert p
 for h in handles:attach(p,h)
 link(p);ok=I();pstatus(p,0x8B82,c.byref(ok));msg=c.create_string_buffer(16000);plog(p,len(msg),None,msg);assert ok.value,(name,msg.value.decode());delp(p)
 for h in handles:dele(h)
 print('PASS Mesa compile/link',name,flush=True)
vert=literal(base/k/'GlesGraphicsShader.kt','INVALID') if False else re.search(r'return """(.*?)"""\.trimIndent\(\)',(base/k/'GlesGraphicsShader.kt').read_text(),re.S)[1];vert=textwrap.dedent(vert).strip('\n')
entries=[('GlesIris26983COnGpuMerge.kt','lensShadeShader','GlesIris26858BNoiseHighlight.kt','bLensShade'),('GlesIris26983COnGpuMerge.kt','iris26876DerivedGuideShader','GlesMgcRawSpatialStacker.kt','iris26876DerivedGuideShader'),('GlesIris26983COnColorContract.kt','applyAmazeWbForLabFcc','GlesIris26856RawrColorContract.kt','applyAmazeWbForLabFcc'),('GlesIris26983COnRawLensMedian.kt','shader','GlesIris26932RawLensMedian.kt','shader'),('GlesIris26983COnSmoothWhite.kt','shader','GlesIris26932LkrSmoothWhite.kt','shader')]
for f,n,bf,bn in entries:
 src=literal(cand/k/f,n);assert src==literal(base/k/bf,bn),(f,n);program([(0x8B31,vert.replace('$version','300')),(0x8B30,src)],f+':'+n)
sharp='GlesIris26983COnGpuSharpest.kt';p=cand/k/sharp
for n in ('vertex','fragment'):assert literal(p,n)==literal(base/k/'GlesIris26870GpuSharpest.kt',n)
program([(0x8B31,literal(p,'vertex')),(0x8B30,literal(p,'fragment'))],'C ON sharpness')
lab=cand/'assets/iris26983/con/lab';common=(lab/'lab_defringe_common.glsl').read_text()
for p in sorted(lab.glob('*.comp')):
 raw=p.read_text();assert raw.count('#include "lab_defringe_common.glsl"')==1;program([(0x91B9,raw.replace('#include "lab_defringe_common.glsl"',common))],p.name)
renderer=(cand/'java/com/particlesdevs/photoncamera/processing/ultrahdr/Iris26983COnGpuFinalRenderer.java').read_text();v=re.search(r'private static final String VERT\s*=\s*(.*?);\s*\n',renderer,re.S)[1];v=''.join(json.loads(x) for x in re.findall(r'"(?:[^"\\]|\\.)*"',v));assert v.startswith('#version 310 es')
p=cand/'assets/shaders/iris26983/con_fused_final_p3_gain.frag';program([(0x8B31,v),(0x8B30,p.read_text())],p.name)
print('PASS 10 real GLES shader programs, source parity; not pinned GLSL/SPIR-V gate')
