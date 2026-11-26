import ctypes as C, pathlib, re, textwrap, sys
import numpy as np
from ctypes import c_int as I,c_uint as U,c_float as F,c_void_p as P,c_char_p as S, POINTER as ptr, byref
root=pathlib.Path(__file__).resolve().parent
file=root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/GpuReferenceGainmapProducer.kt'
s=file.read_text()
shaders=[textwrap.dedent(re.search(r'private val '+name+r' = """\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S).group(1)) for name in ('VERTEX_SHADER','RAW_LUMA_RESIDUAL_FRAGMENT_SHADER')]
e=C.CDLL('libEGL.so.1')
def egl(name,ret,*args):
 f=getattr(e,name);f.restype=ret;f.argtypes=list(args);return f
get=egl('eglGetProcAddress',P,S)
def gl(name,ret,*args):
 p=get(name.encode());assert p,name;return C.CFUNCTYPE(ret,*args)(p)
getplat=C.CFUNCTYPE(P,U,P,ptr(I))(get(b'eglGetPlatformDisplayEXT'))
d=getplat(0x31DD,None,None); assert d
major=I();minor=I();assert egl('eglInitialize',U,P,ptr(I),ptr(I))(d,byref(major),byref(minor))
assert egl('eglBindAPI',U,U)(0x30A0)
attrs=(I*13)(0x3033,1,0x3040,0x40,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038)
conf=P();n=I();assert egl('eglChooseConfig',U,P,ptr(I),ptr(P),I,ptr(I))(d,attrs,byref(conf),1,byref(n)) and n.value
ctx=egl('eglCreateContext',P,P,P,P,ptr(I))(d,conf,None,(I*3)(0x3098,3,0x3038));assert ctx
surf=egl('eglCreatePbufferSurface',P,P,P,ptr(I))(d,conf,(I*5)(0x3057,64,0x3056,64,0x3038));assert surf
assert egl('eglMakeCurrent',U,P,P,P,P)(d,surf,surf,ctx)
print('EGL',major.value,minor.value,'GL',gl('glGetString',S,U)(0x1F02).decode(),'renderer',gl('glGetString',S,U)(0x1F01).decode())
create=gl('glCreateShader',U,U);source=gl('glShaderSource',None,U,I,ptr(S),ptr(I));compile=gl('glCompileShader',None,U);getiv=gl('glGetShaderiv',None,U,U,ptr(I));getlog=gl('glGetShaderInfoLog',None,U,I,ptr(I),P)
ids=[]
for typ,src in zip((0x8B31,0x8B30),shaders):
 sh=create(typ);p=S(src.encode());source(sh,1,byref(p),None);compile(sh);status=I();getiv(sh,0x8B81,byref(status));log=C.create_string_buffer(4096);getlog(sh,4096,None,log);assert status.value,log.value;ids.append(sh)
prog=gl('glCreateProgram',U)();attach=gl('glAttachShader',None,U,U)
for sh in ids: attach(prog,sh)
gl('glLinkProgram',None,U)(prog);status=I();gl('glGetProgramiv',None,U,U,ptr(I))(prog,0x8B82,byref(status));log=C.create_string_buffer(4096);gl('glGetProgramInfoLog',None,U,I,ptr(I),P)(prog,4096,None,log);assert status.value,log.value
print('PASS exact runtime ESSL 300 vertex+fragment compile/link (host Mesa, not pinned Actions glslang/SPIR-V)')
gl('glUseProgram',None,U)(prog)
loc=gl('glGetUniformLocation',I,U,S);setf=gl('glUniform1f',None,I,F);seti=gl('glUniform1i',None,I,I)
for name,v in [(b'uMinGainRatio',1),(b'uMaxGainRatio',2),(b'uOffset',0.0001),(b'uStrength',1)]:setf(loc(prog,name),v)
# Test GPU inputs use the same transfer domains as the production shader.
sdr=np.ones((64,64,4),np.float32);hdr=sdr.copy();lut=sdr.copy()
sdr[:,:,:3]=((np.arange(64)*255//63)/255)[None,:,None]
hdr[:,:,:3]=(np.arange(64)/8)[:,None,None]
texs=(U*3)();gl('glGenTextures',None,I,ptr(U))(3,texs)
for i,(name,array) in enumerate([(b'uLutLuminanceGainTexture',lut),(b'uSdrTexture',sdr),(b'uHdrTexture',hdr)]):
 gl('glActiveTexture',None,U)(0x84C0+i);gl('glBindTexture',None,U,U)(0x0DE1,texs[i]);seti(loc(prog,name),i)
 for param,val in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812F),(0x2803,0x812F)]:gl('glTexParameteri',None,U,U,I)(0x0DE1,param,val)
 gl('glTexImage2D',None,U,I,I,I,I,I,U,U,P)(0x0DE1,0,0x8814,64,64,0,0x1908,0x1406,array.ctypes.data)
# Fullscreen quad with explicit UVs; 1-to-1 input grid to eliminate sampling ambiguity.
vertices=np.array([[-1,-1,0,0],[1,-1,1,0],[-1,1,0,1],[1,1,1,1]],np.float32)
vao=U();gl('glGenVertexArrays',None,I,ptr(U))(1,byref(vao));gl('glBindVertexArray',None,U)(vao)
buf=U();gl('glGenBuffers',None,I,ptr(U))(1,byref(buf));gl('glBindBuffer',None,U,U)(0x8892,buf);gl('glBufferData',None,U,C.c_ssize_t,P,U)(0x8892,vertices.nbytes,vertices.ctypes.data,0x88E4)
for name,offset in [(b'aPosition',0),(b'aTexCoord',8)]:
 a=gl('glGetAttribLocation',I,U,S)(prog,name);assert a>=0;gl('glEnableVertexAttribArray',None,U)(a);gl('glVertexAttribPointer',None,U,I,U,U,I,P)(a,2,0x1406,0,16,P(offset))
gl('glViewport',None,I,I,I,I)(0,0,64,64);gl('glDrawArrays',None,U,I,I)(0x0005,0,4)
result=np.empty((64,64,4),np.uint8);gl('glReadPixels',None,I,I,I,I,U,U,P)(0,0,64,64,0x1908,0x1401,result.ctypes.data)
err=gl('glGetError',U)();assert err==0,hex(err)
reference=np.array([float(x) for x in pathlib.Path(sys.argv[1]).read_text().splitlines()[1:]]).reshape(64,64)
quant=np.rint(reference*255).astype(int); actual=result[:,:,0].astype(int)
assert np.max(np.abs(actual-quant))<=1,(np.max(np.abs(actual-quant)),actual,quant)
assert np.array_equal(result[:,:,0],result[:,:,1]) and np.array_equal(result[:,:,0],result[:,:,2])
assert np.all(actual[reference==0]==0)
print('PASS 4096 actual GPU output samples versus compiled Kotlin; maximum encoded 8-bit code error',np.max(np.abs(actual-quant)))
