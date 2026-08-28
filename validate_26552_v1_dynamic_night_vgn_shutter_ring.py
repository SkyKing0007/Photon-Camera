#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import hashlib, re, sys, tempfile, shutil, xml.etree.ElementTree as ET

ALLOW = [
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java',
'app/src/main/res/xml/preferences.xml',
'app/version.properties',
]

def die(msg): raise SystemExit('FAIL: '+msg)
def need(cond,msg):
    if not cond: die(msg)
def text(root, rel): return (Path(root)/rel).read_text()
def h(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tree(root):
    root=Path(root); out={}
    for p in root.rglob('*'):
        if p.is_file(): out[p.relative_to(root).as_posix()]=h(p)
    return out

def changed(base,cand):
    b,c=tree(base),tree(cand)
    return sorted(k for k in set(b)|set(c) if b.get(k)!=c.get(k))

def raw_strings(src):
    # Named Kotlin triple strings in the VGN shader object.
    out={}
    pat=re.compile(r'(?m)^\s*(?:private\s+)?val\s+(\w+)\s*=\s*"""\n(.*?)\n\s*"""\.trimIndent\(\)',re.S)
    for m in pat.finditer(src): out[m.group(1)]=m.group(2)
    return out

def mask_raw(src,names):
    for name in names:
        pat=re.compile(r'(?m)^(\s*(?:private\s+)?val\s+'+re.escape(name)+r'\s*=\s*"""\n).*?(\n\s*"""\.trimIndent\(\))',re.S)
        src,n=pat.subn(r'\1<IRIS_MASKED_'+name+r'>\2',src,count=1)
        need(n==1,'cannot mask Kotlin raw string '+name)
    return src

def extract_block(src,start,end):
    a=src.find(start); need(a>=0,'missing start anchor '+start)
    b=src.find(end,a); need(b>a,'missing end anchor '+end)
    return src[a:b]

def check_delimiters(src,label):
    # GLSL exact-expanded source has no string literals. Strip comments and check structural pairs.
    s=re.sub(r'/\*.*?\*/','',src,flags=re.S)
    s=re.sub(r'//.*','',s)
    pairs={')':'(',']':'[','}':'{'}; st=[]
    for ch in s:
        if ch in '([{': st.append(ch)
        elif ch in pairs:
            need(st and st[-1]==pairs[ch],f'{label}: delimiter mismatch at {ch}')
            st.pop()
    need(not st,f'{label}: unclosed delimiter {st[-1] if st else "?"}')

# Complete-enough GLSL ES keyword/reserved set for identifier declarations.  This is a
# supplemental precompiler regression gate; pinned glslangValidator remains authoritative.
GLSL_RESERVED = set("""
attribute const uniform varying buffer shared coherent volatile restrict readonly writeonly
atomic_uint layout centroid flat smooth noperspective patch sample break continue do for while
switch case default if else subroutine in out inout float double int void bool true false
invariant precise discard return mat2 mat3 mat4 dmat2 dmat3 dmat4 mat2x2 mat2x3 mat2x4
mat3x2 mat3x3 mat3x4 mat4x2 mat4x3 mat4x4 dmat2x2 dmat2x3 dmat2x4 dmat3x2 dmat3x3
dmat3x4 dmat4x2 dmat4x3 dmat4x4 vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4
uvec2 uvec3 uvec4 dvec2 dvec3 dvec4 lowp mediump highp precision sampler1D sampler2D
sampler3D samplerCube sampler1DShadow sampler2DShadow samplerCubeShadow sampler1DArray
sampler2DArray sampler1DArrayShadow sampler2DArrayShadow isampler1D isampler2D isampler3D
isamplerCube isampler1DArray isampler2DArray usampler1D usampler2D usampler3D usamplerCube
usampler1DArray usampler2DArray sampler2DRect sampler2DRectShadow isampler2DRect usampler2DRect
samplerBuffer isamplerBuffer usamplerBuffer sampler2DMS isampler2DMS usampler2DMS
sampler2DMSArray isampler2DMSArray usampler2DMSArray image1D iimage1D uimage1D image2D
iimage2D uimage2D image3D iimage3D uimage3D image2DRect iimage2DRect uimage2DRect
imageCube iimageCube uimageCube imageBuffer iimageBuffer uimageBuffer image1DArray iimage1DArray
uimage1DArray image2DArray iimage2DArray uimage2DArray image2DMS iimage2DMS uimage2DMS
image2DMSArray iimage2DMSArray uimage2DMSArray struct common partition active asm class union
enum typedef template this resource goto inline noinline public static extern external interface long
short half fixed unsigned superp input output hvec2 hvec3 hvec4 fvec2 fvec3 fvec4 sampler3DRect
filter sizeof cast namespace using row_major
""".split())
GLSL_TYPES = set(x for x in GLSL_RESERVED if re.match(r'^(?:[diub]?vec[234]|[d]?mat[234](?:x[234])?|[iu]?sampler|[iu]?image|atomic_uint|float|double|int|uint|bool|void)', x))
GLSL_TYPES |= {'float','double','int','uint','bool','void'}

def glsl_declared_reserved(src,label):
    # Strip comments and preprocessor payloads only after separately checking macro identifiers.
    for m in re.finditer(r'(?m)^\s*#\s*define\s+([A-Za-z_]\w*)',src):
        if m.group(1) in GLSL_RESERVED:
            die(f'{label}: reserved GLSL identifier used as macro name: {m.group(1)}')
    clean=re.sub(r'/\*.*?\*/',' ',src,flags=re.S)
    clean=re.sub(r'//[^\n]*',' ',clean)
    # Include user-defined struct names as types, then catch declarations/functions/parameters/fields.
    types=set(GLSL_TYPES)
    types.update(re.findall(r'\bstruct\s+([A-Za-z_]\w*)',clean))
    tpat='|'.join(sorted(map(re.escape,types),key=len,reverse=True))
    # Qualifiers may precede a type; declaration identity is the token immediately following the type.
    pat=re.compile(r'\b(?:'+tpat+r')\s+([A-Za-z_]\w*)\b')
    bad=[]
    for m in pat.finditer(clean):
        ident=m.group(1)
        if ident in GLSL_RESERVED:
            line=clean.count('\n',0,m.start(1))+1
            bad.append((line,ident))
    if bad:
        die(f'{label}: reserved GLSL identifier declaration(s): {bad}')
    # Permanent regression from Actions run 33143071632 / job 98758015139.
    need(not re.search(r'\bfloat\s+coherent\b',clean),f'{label}: 26552 V1 Actions regression float coherent reintroduced')

def check_glsl_dir(root):
    root=Path(root); files=sorted(root.glob('*.comp')); need(files,'no expanded .comp shaders for reserved scan')
    for p in files: glsl_declared_reserved(p.read_text(),p.name)
    print('PASS: complete declared-identifier GLSL reserved-keyword scan; 26552 V1 coherent regression blocked')

def selftest():
    for req in range(-1000,1001):
        total=max(2,min(50,req)); lng=0 if total==2 else max(1,(total+2)//5); short=total-lng
        need(short>=2 and lng>=0 and short+lng==total,'formula selftest')
    need((12,3)==(15-max(1,(15+2)//5),max(1,(15+2)//5)),'15 formula')
    need((16,4)==(20-max(1,(20+2)//5),max(1,(20+2)//5)),'20 formula')
    need((40,10)==(50-max(1,(50+2)//5),max(1,(50+2)//5)),'50 formula')
    glsl_declared_reserved('#version 310 es\nvoid main(){ float coherentSupport=1.0; }\n','reserved-selftest-good')
    try:
        glsl_declared_reserved('#version 310 es\nvoid main(){ float coherent=1.0; }\n','reserved-selftest-bad')
    except SystemExit:
        pass
    else:
        die('reserved keyword selftest failed to reject float coherent')
    print('PASS: validator self-test')

def main(base,cand):
    base=Path(base); cand=Path(cand)
    need(base.is_dir() and cand.is_dir(),'base/candidate missing')
    ch=changed(base,cand)
    need(ch==ALLOW,'changed-file allowlist mismatch\n got='+repr(ch)+'\nwant='+repr(ALLOW))

    # Version is controlled and isolated to the candidate.
    need('VERSION_NAME=0.9726551' in text(base,'app/version.properties'),'base version name')
    need('VERSION_BUILD=26551' in text(base,'app/version.properties'),'base version build')
    cv=text(cand,'app/version.properties')
    need('VERSION_NAME=0.9726552' in cv and 'VERSION_BUILD=26552' in cv,'candidate version/build')

    selector=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightFrameSelector.java')
    for x in ['MIN_NIGHT_FRAMES = 2','MAX_NIGHT_FRAMES = 50','total == 2 ? 0 : Math.max(1, (total + 2) / 5)','return index < shortFrames','IRIS_26552_NIGHT_DYNAMIC_2_TO_50_FRAME_OWNER']:
        need(x in selector,'selector contract missing '+x)
    need(not re.search(r'\b(SHORT_FRAMES|LONG_FRAMES|TOTAL_FRAMES)\b',selector),'fixed Night selector constants survived')

    pref=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java')
    need('return Math.max(1, Math.min(50, persisted));' in pref,'runtime frame preference clamp missing')
    xml_path=cand/'app/src/main/res/xml/preferences.xml'
    try: ET.parse(xml_path)
    except Exception as e: die('preferences.xml parse: '+str(e))
    xml=xml_path.read_text()
    seek=re.search(r'<com\.particlesdevs\.photoncamera\.ui\.settings\.custompreferences\.UniversalSeekBarPreference[^>]*pref_frame_count_key[^>]*/>',xml)
    need(seek is not None,'frame slider XML missing')
    need('maxValue="50"' in seek.group(0) and 'minValue="1"' in seek.group(0),'frame slider 1..50 mismatch')

    exp_b=text(base,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java')
    exp=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/parameters/IrisNightExposureSelector.java')
    for x in ['boolean requireLongExposure','if (!requireLongExposure)','IRIS_26552_NIGHT_2_SHORT_ONLY_EXPOSURE','longRequested=false','IRIS_26552_NIGHT_DYNAMIC_EXPOSURE']:
        need(x in exp,'exposure dynamic contract missing '+x)
    # Prove the established Long derivation math itself is byte-identical.
    long_b=extract_block(exp_b,'        long longCap =','        Log.i(TAG, "IRIS_26541_NIGHT_12_PLUS_3_EXPOSURE"')
    long_c=extract_block(exp,'        long longCap =','        Log.i(TAG, "IRIS_26552_NIGHT_DYNAMIC_EXPOSURE"')
    need(long_b==long_c,'proven Long +2EV/shake/anti-flicker derivation changed')
    rb=re.search(r'(?m)^\s*private static final [^;]*\bLONG_TARGET_MULTIPLIER\b[^;]*;',exp_b)
    rc=re.search(r'(?m)^\s*private static final [^;]*\bLONG_TARGET_MULTIPLIER\b[^;]*;',exp)
    need(rb and rc and rb.group(0)==rc.group(0),'Long target constant drift')
    for helper,next_anchor in [('shortMotionCap','    // Long frames are deliberately'),('longMotionCap','    private static long antiFlicker'),('antiFlicker','    public static Plan freezePlan')]:
        start='    private static long '+helper
        need(extract_block(exp_b,start,next_anchor)==extract_block(exp,start,next_anchor),'exposure helper drift '+helper)

    cap=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java')
    for x in [
        'IRIS_26552_NIGHT_FROZEN_FRAME_PLAN_OWNER',
        'IrisNightFrameSelector.freezePlan(iris26540RequestedFrames)',
        'mPreviewCaptureResult, iris26552NightFramePlan.longFrames > 0)',
        '? iris26552NightFramePlan.totalFrames',
        'prepareIrisNight26540CaptureState(iris26552NightFramePlan',
        'iris26552NightFramePlan.isShortFrame(i)',
        'frozenFramePlan.shortFrames, frozenFramePlan.longFrames',
        'IRIS_26552_NIGHT_REQUEST_BUDGET_IMMUTABLE_AT_SEQUENCE_END',
        'mIrisNight26552FramePlan = null;',
        '(long)mIrisNight26540ExpectedFrames - 1L) * capacity',
    ]: need(x in cap,'capture ownership missing '+x)
    need('mIrisNight26540ExpectedFrames = finalFrameCount;' not in cap,'sequence completion overwrites shutter-frozen budget')
    need(not re.search(r'IrisNightFrameSelector\.(SHORT_FRAMES|LONG_FRAMES|TOTAL_FRAMES)',cap),'CaptureController fixed Night constants survived')
    night_count_branch='int frameCount = iris26533CaptureMode == CameraMode.NIGHT\n                    ? iris26552NightFramePlan.totalFrames\n                    : FrameNumberSelector.getFrames();'
    need(night_count_branch in cap,'Night is not isolated from legacy FrameNumberSelector')

    batch=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisNightBatch.java')
    for x in ['requestedShortFrames','requestedLongFrames','shortCount != requestedShortFrames || longCount != requestedLongFrames','frameBudget != frames.size()','IRIS_26552_NIGHT_IMMUTABLE_DYNAMIC_BATCH_OWNER']:
        need(x in batch,'immutable batch contract missing '+x)
    need('requestedShortFrames + requestedLongFrames > IrisNightFrameSelector.MAX_NIGHT_FRAMES' in batch,'batch 50-frame upper bound missing')

    # Night downstream and Sabre ownership are protected because none of their files are allowed to change.
    for rel in [
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightProcessor.java',
        'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
        'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
    ]:
        need((base/rel).read_bytes()==(cand/rel).read_bytes(),'protected Night/Sabre path changed '+rel)
    sabre=text(cand,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    need('frameCount < 52 -> 51f' in sabre,'50-frame MGC/Sabre frame-weight bucket missing')
    need('normalFrameCount >= 1 && normalFrameCount + shadowLongFrameCount == frames.size' in sabre,'Sabre 2+0 role compatibility missing')

    ui_b=text(base,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
    ui=text(cand,'app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java')
    for x in [
        'IRIS_26552_NIGHT_SHUTTER_RING_Z_ORDER',
        'ownerMode == CameraMode.NIGHT\n                ? this.mProcessingProgressBar : this.mCaptureProgressBar',
        'IRIS_26552_NIGHT_SHUTTER_CAPTURE_RING',
        'IRIS_26552_NIGHT_NO_OVERSIZED_VIEWFINDER_RING',
        'layoutViewfinder.frameTimer.setVisibility(View.INVISIBLE)',
        'layoutViewfinder.captureProgressBar.setVisibility(View.INVISIBLE)',
        'bottombuttons.frameCount.bringToFront()',
    ]: need(x in ui,'Night ring/UI contract missing '+x)
    # 26551 stale-callback generation method remains unchanged.
    for name in ['iris26551AdvanceProgressUiGeneration','iris26551ProgressUiIsCurrent']:
        def method(src,n):
            m=re.search(r'(?m)^\s*private\s+[^\n]*\b'+re.escape(n)+r'\([^\n]*\)\s*\{',src); need(m is not None,'missing '+n)
            i=m.start(); j=m.end(); depth=1
            while j<len(src) and depth:
                if src[j]=='{': depth+=1
                elif src[j]=='}': depth-=1
                j+=1
            need(depth==0,'unclosed method '+n); return src[i:j]
        need(method(ui_b,name)==method(ui,name),'26551 generation protection changed '+name)

    vrel='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt'
    vb=text(base,vrel); vc=text(cand,vrel)
    rsb,rsc=raw_strings(vb),raw_strings(vc)
    need(set(rsb)==set(rsc),'VGN shader inventory changed')
    modified=[n for n in sorted(rsb) if rsb[n]!=rsc[n]]
    need(modified==['directionalSmooth','iirRgb'],'unexpected embedded GLSL delta '+repr(modified))
    need(mask_raw(vb,modified)==mask_raw(vc,modified),'VGN host/non-modified source drifted')
    for x in ['IRIS_26552_VGN_REAL_COLOR_GEOMETRY_SUPPORT','IRIS_26552_VGN_LOW_CHROMA_CROSS_EDGE_CONTAINMENT','float vectorAgreement=','float coherentSupport=','return support*(1.0-highlightBoundary(p));','expansionGuard=lowOriginal*localLumaEdge(p)*expansion*(1.0-highlight)']:
        need(x in vc,'directional VGN guard missing '+x)
    for x in ['iirRealColorSupport','iirHighlightBoundary','iirLumaEdge','effectiveStrength*=artifactConfidence*(1.0-0.85*preserve)','expansionGuard=lowOriginal*iirLumaEdge(p)*expansion*(1.0-highlight)']:
        need(x in vc,'IIR3 VGN guard missing '+x)
    # Never add named-color branches or a saturation/gain multiplier in the new delta.
    new_delta='\n'.join(re.findall(r'IRIS_26552[^\n]*|.*vectorAgreement.*|.*expansionGuard.*|.*realColor.*|.*highlightBoundary.*',vc,re.I))
    need(not re.search(r'\b(red|blue|green|magenta|cyan|yellow)\b\s*[<>=]',new_delta,re.I),'named-color branch added')
    need('saturationBoost' not in vc and 'globalSaturation' not in vc,'global saturation boost added')

    # Production reachability of the shared VGN owner is unchanged and explicit in both engines.
    for rel in ['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26521SpatialRgbStacker.kt','app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt']:
        s=text(cand,rel); need('GlesIris26529SpatialRgbChromaPostprocessor' in s,'VGN owner not production-reachable '+rel)
    need('linkComputeProgram(Iris26529SpatialRgbChromaShaders.directionalSmooth' in vc,'directional shader not linked')
    need('linkComputeProgram(Iris26529SpatialRgbChromaShaders.iirRgb' in vc,'IIR shader not linked')

    print('PASS: exact 9-file runtime scope')
    print('PASS: dynamic Night 2..50 shutter-frozen frame/exposure ownership')
    print('PASS: N=2 skips Long derivation; N>=3 proven Long math byte-identical')
    print('PASS: immutable exact requested/actual role contract')
    print('PASS: 26551 generation/lifecycle protection retained; Night shutter-ring routing isolated')
    print('PASS: VGN host unchanged; only exact directionalSmooth + iirRgb runtime shader strings changed')
    print('PASS: strong-highlight VGN authority + real-color/low-chroma geometry guards')
    print('PASS: protected Night/Sabre processing bytes and 50-frame MGC bucket invariant')

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--self-test': selftest()
    elif len(sys.argv)==3 and sys.argv[1]=='--check-glsl': check_glsl_dir(sys.argv[2])
    elif len(sys.argv)==3: main(sys.argv[1],sys.argv[2])
    else: raise SystemExit('usage: validate...py --self-test | --check-glsl <expanded-dir> | <base> <candidate>')
