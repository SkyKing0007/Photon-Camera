"""Compile and render the actual expanded GLES3 shader, not a copied implementation."""
import ctypes as C, pathlib, re, textwrap, sys, json
import numpy as np
from ctypes import c_int as I,c_uint as U,c_float as F,c_void_p as P,c_char_p as S, POINTER as ptr, byref
from scipy.interpolate import PchipInterpolator
R=pathlib.Path(__file__).resolve().parent
root=pathlib.Path(sys.argv[1]).resolve()
K=root/'app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129'
def literal(f,n):
 s=f.read_text();m=re.search(r'\bval '+n+r' = """\n(.*?)\n\s*"""\.trimIndent\(\)',s,re.S);assert m,(f,n);return textwrap.dedent(m.group(1))
vert=literal(K/'raw/RawFullscreenQuad.kt','VERTEX_SHADER');frag=literal(K/'raw/RawAdjustmentPass.kt','FRAGMENT_SHADER').replace('${ShadowsHighlightsShader.GLSL}',literal(K/'lut/ShadowsHighlightsShader.kt','GLSL'))
assert '${' not in frag
shaders=[vert,frag]
# Exact original GLES source expansion and host Mesa real compile/link.
e=C.CDLL('libEGL.so.1')
def egl(name,ret,*args):
 f=getattr(e,name);f.restype=ret;f.argtypes=list(args);return f
get=egl('eglGetProcAddress',P,S)
def gl(name,ret,*args):
 p=get(name.encode());assert p,name;return C.CFUNCTYPE(ret,*args)(p)
getplat=C.CFUNCTYPE(P,U,P,ptr(I))(get(b'eglGetPlatformDisplayEXT'))
d=getplat(0x31DD,None,None);assert d
major=I();minor=I();assert egl('eglInitialize',U,P,ptr(I),ptr(I))(d,byref(major),byref(minor))
assert egl('eglBindAPI',U,U)(0x30A0)
attrs=(I*13)(0x3033,1,0x3040,0x40,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038)
conf=P();n=I();assert egl('eglChooseConfig',U,P,ptr(I),ptr(P),I,ptr(I))(d,attrs,byref(conf),1,byref(n)) and n.value
ctx=egl('eglCreateContext',P,P,P,P,ptr(I))(d,conf,None,(I*3)(0x3098,3,0x3038));assert ctx
surf=egl('eglCreatePbufferSurface',P,P,P,ptr(I))(d,conf,(I*5)(0x3057,256,0x3056,256,0x3038));assert surf
assert egl('eglMakeCurrent',U,P,P,P,P)(d,surf,surf,ctx)
print('EGL',major.value,minor.value,'GL',gl('glGetString',S,U)(0x1F02).decode(),'renderer',gl('glGetString',S,U)(0x1F01).decode(),flush=True)
create=gl('glCreateShader',U,U);source=gl('glShaderSource',None,U,I,ptr(S),ptr(I));compile=gl('glCompileShader',None,U);getiv=gl('glGetShaderiv',None,U,U,ptr(I));getlog=gl('glGetShaderInfoLog',None,U,I,ptr(I),P)
ids=[]
for typ,src in zip((0x8B31,0x8B30),shaders):
 sh=create(typ);p=S(src.encode());source(sh,1,byref(p),None);compile(sh);status=I();getiv(sh,0x8B81,byref(status));log=C.create_string_buffer(8192);getlog(sh,8192,None,log);assert status.value,log.value;ids.append(sh)
prog=gl('glCreateProgram',U)();attach=gl('glAttachShader',None,U,U)
for sh in ids:attach(prog,sh)
gl('glLinkProgram',None,U)(prog);status=I();gl('glGetProgramiv',None,U,U,ptr(I))(prog,0x8B82,byref(status));log=C.create_string_buffer(8192);gl('glGetProgramInfoLog',None,U,I,ptr(I),P)(prog,8192,None,log);assert status.value,log.value
print('PASS actual expanded RawAdjustmentPass ESSL300 vertex+fragment compile/link',flush=True)
gl('glUseProgram',None,U)(prog)
loc=gl('glGetUniformLocation',I,U,S);setf=gl('glUniform1f',None,I,F);seti=gl('glUniform1i',None,I,I)
for name in (b'uHighlights',b'uShadows',b'uBlacks',b'uWhites'):setf(loc(prog,name),0)
seti(loc(prog,b'uToneBaseOnly'),0);seti(loc(prog,b'uInputTexture'),0)
seti(loc(prog,b'uIris26993COffShadowLift'),1)
mat=np.eye(4,dtype=np.float32);gl('glUniformMatrix4fv',None,I,I,U,P)(loc(prog,b'uTexMatrix'),1,0,mat.ctypes.data)
W=H=256;rng=np.random.default_rng(26993)
arr=np.ones((H,W,4),np.float32);arr[:,:,:3]=rng.random((H,W,3))**4
arr[:128,:,:3]=np.geomspace(1e-9,1,128*W).reshape(128,W,1)
arr[128,0,:3]=0;arr[128,1,:3]=1;arr[128,2,:3]=[1.,.001,.001];arr[128,3,:3]=[1.5,0,0];arr[128,4,:3]=[-.01,.01,.02]
tex=(U*2)();gl('glGenTextures',None,I,ptr(U))(2,tex)
def texture(i,data):
 gl('glActiveTexture',None,U)(0x84C0+i);gl('glBindTexture',None,U,U)(0x0DE1,tex[i])
 for param,val in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812F),(0x2803,0x812F)]:gl('glTexParameteri',None,U,U,I)(0x0DE1,param,val)
 gl('glTexImage2D',None,U,I,I,I,I,I,U,U,P)(0x0DE1,0,0x8814,W,H,0,0x1908,0x1406,data.ctypes.data if data is not None else None)
texture(0,arr);texture(1,None)
fbo=U();gl('glGenFramebuffers',None,I,ptr(U))(1,byref(fbo));gl('glBindFramebuffer',None,U,U)(0x8D40,fbo);gl('glFramebufferTexture2D',None,U,U,U,U,I)(0x8D40,0x8CE0,0x0DE1,tex[1],0);assert gl('glCheckFramebufferStatus',U,U)(0x8D40)==0x8CD5
vertices=np.array([[-1,-1,0,0],[1,-1,1,0],[-1,1,0,1],[1,1,1,1]],np.float32);vao=U();gl('glGenVertexArrays',None,I,ptr(U))(1,byref(vao));gl('glBindVertexArray',None,U)(vao);buf=U();gl('glGenBuffers',None,I,ptr(U))(1,byref(buf));gl('glBindBuffer',None,U,U)(0x8892,buf);gl('glBufferData',None,U,C.c_ssize_t,P,U)(0x8892,vertices.nbytes,vertices.ctypes.data,0x88E4)
for name,offset in [(b'aPosition',0),(b'aTexCoord',8)]:
 a=gl('glGetAttribLocation',I,U,S)(prog,name);assert a>=0;gl('glEnableVertexAttribArray',None,U)(a);gl('glVertexAttribPointer',None,U,I,U,U,I,P)(a,2,0x1406,0,16,P(offset))
gl('glViewport',None,I,I,I,I)(0,0,W,H)
def draw(enabled):
 seti(loc(prog,b'uIris26993COffShadowLift'),enabled);gl('glDrawArrays',None,U,I,I)(0x0005,0,4);result=np.empty_like(arr);gl('glReadPixels',None,I,I,I,I,U,U,P)(0,0,W,H,0x1908,0x1406,result.ctypes.data);err=gl('glGetError',U)();assert err==0,hex(err);return result
# Baseline identity on all finite inputs, including extended/signed values.
a=draw(0);assert np.array_equal(a,arr),(np.max(np.abs(a-arr)),a[0,0],arr[0,0]);print('PASS disabled shader exact identity 65,536 RGB samples')
a=draw(1);rgb=arr[:,:,:3];y=rgb.astype(float)@np.array([.2126,.7152,.0722]);k=json.loads((R/'26993_shadow_curve.json').read_text());spl=PchipInterpolator(k['log2_knots'],k['ev']);ev=spl(np.log2(np.clip(y,.0001,1)));gain=np.minimum(2**ev,np.maximum(1,1/np.maximum(rgb.max(axis=-1),1e-8)));expected=rgb*gain[:,:,None];err=float(np.max(np.abs(a[:,:,:3]-expected)));assert err<2e-6,err
assert np.array_equal(a[:,:,:3][(y<=.0005)|(y>=.65)],rgb[(y<=.0005)|(y>=.65)])
assert np.min(np.diff(a[:128,:,0].ravel()))>=-1e-7
assert np.max(a[:,:,:3][(rgb>=0).all(axis=-1)&(rgb<=1).all(axis=-1)])<=1.000001
print('PASS 65,536 actual GPU RGB outputs vs approved PCHIP preview; max absolute float error',err)
print('PASS true black/deep floor/highlights exact identity; neutral monotonicity; gamut cap; signed/extended safety')
# Dense double precision analytical proof on original approved PCHIP and monotonicity.
z=np.geomspace(1e-9,1,1000000);g=spl(np.log2(np.clip(z,.0001,1)));assert np.all(np.diff(z*2**g)>0);assert np.max(g)<=1.350001;print('PASS 1,000,000 dense approved curve samples; max gain 1.35 EV')
