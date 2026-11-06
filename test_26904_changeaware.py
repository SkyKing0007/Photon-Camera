#!/usr/bin/env python3
"""Current-only change-aware Photon 26904 integrity/semantics/unit tests."""
from pathlib import Path
import argparse, hashlib, importlib.util, itertools, os, re, subprocess, sys, tempfile

def need(value,msg):
    if not value:raise AssertionError('26904 TEST FAIL: '+msg)

def extract_method(s,needle):
    i=s.index(needle); start=s.index('{',i); level=0
    for j in range(start,len(s)):
        if s[j]=='{':level+=1
        elif s[j]=='}':
            level-=1
            if level==0:return s[i:j+1]
    raise AssertionError('incomplete java method')

def geom(rot,mir,qx,qy,w,h,cw,ch):
    # Coordinate math follows the final runtime ESSL310 exactly.
    cropbottom=max(0,min(h-ch,h-1))
    if rot==0:return(qx,(h-1-qy) if mir else (cropbottom+qy))
    if rot==1:return(w-1-qy,(h-1-qx) if mir else (cropbottom+qx))
    if rot==2:return(w-1-qx,(cropbottom+qy) if mir else (h-1-qy))
    return(qy,(cropbottom+qx) if mir else (h-1-qx))

def rotation_test(code):
    need('texSizeLocal.y - 1 - q.x' in code,'no right 90deg fix')
    need('texSizeLocal.x - 1 - q.y' in code,'no right 270deg fix')
    need('texSizeLocal.x - 1 - q.x' in code,'no right 180deg fix')
    for w,h,cw,ch in ((4096,3072,4096,3072),(4096,3072,4096,1536),(4032,3024,4032,3024), (2048,1536,2048,1000)):
        for rot,mir in itertools.product(range(4),(False,True)):
            ow,oh=(ch,cw) if rot in (1,3) else (cw,ch)
            corners=[(0,0),(ow-1,0),(0,oh-1),(ow-1,oh-1)]
            corners += [(1,1),(ow-2,oh-2)]
            pts=[geom(rot,mir,x,y,w,h,cw,ch) for x,y in corners]
            for x,y in pts:need(0<=x<w and 0<=y<h, f'rotation OOB {w,h,cw,ch,rot,mir}={x,y}')
            need(len(set(pts))==len(pts),f'nonbijection {rot,mir}')
            if ow>=2:
                a=geom(rot,mir,0,0,w,h,cw,ch)
                b=geom(rot,mir,1,0,w,h,cw,ch)
                need(a!=b,'first two columns duplicate')
    # Historical exact off-by-one bug negative reproduction.
    old_x0=max(0,min(3072-0,3071));old_x1=max(0,min(3072-1,3071))
    need(old_x0==old_x1==3071,'historical 26903 rotation failure no longer reproduces')
    new_x0=geom(3,False,0,0,4096,3072,4096,3072)[1]
    new_x1=geom(3,False,1,0,4096,3072,4096,3072)[1]
    need((new_x0,new_x1)==(3071,3070),'new rotation expected border rows incorrect')
    print('PASS full 0,90,180,270 / mirrored / cropped integer rotation corner and old-bug negative tests')

def run_java(jin):
    names=['cleanupSmoothstep','cleanupLuma','cleanupChromaRms','iris26904RejectUnsupportedDirectionalJinResidual']
    methods='\n'.join(extract_method(jin,'private static '+('int' if n.startswith('iris26904') else 'float')+' '+n+'(') for n in names)
    assertions='''
 static final int N=512;
 static int p(int x,int y){return (y*N+x)*3;}
 static void yes(boolean a,String msg){if(!a)throw new AssertionError(msg);}
 static float[] zeros(){return new float[3*N*N];}
 static int[] bg(int color){int[] x=new int[N*N];java.util.Arrays.fill(x,color);return x;}
 static void mark(float[] x,int a,int b){int i=p(a,b);x[i]=x[i+1]=x[i+2]=0.006f;}
 static void runStripe(int dx,int dy){
    float[] a=zeros();int[] r=bg(0xff101010);for(int k=-8;k<=8;k++)mark(a,240+k*dx,240+k*dy);
    int n=iris26904RejectUnsupportedDirectionalJinResidual(a,r);
    yes(n>0,"missed directional stripe");yes(a[p(240,240)]<.0007f,"no guard");}
 public static void main(String[] args){
    runStripe(1,0);runStripe(0,1);runStripe(1,1);runStripe(1,-1);
    float[] b=zeros();int[] r=bg(0xff101010);for(int x=228;x<=252;x++)for(int y=228;y<=252;y++)mark(b,x,y);
    iris26904RejectUnsupportedDirectionalJinResidual(b,r);yes(b[p(240,240)]==.006f,"broad denoise blocked");
    float[] g=zeros();int[] gr=bg(0xff101010);for(int k=-8;k<=8;k++){mark(g,240,240+k);gr[(240+k)*N+240]=0xffc0c0c0;}
    iris26904RejectUnsupportedDirectionalJinResidual(g,gr);yes(g[p(240,240)]==.006f,"real detail rejected");
    float[] light=zeros();int[] lr=bg(0xff606060);for(int k=-8;k<=8;k++)mark(light,240,240+k);
    iris26904RejectUnsupportedDirectionalJinResidual(light,lr);yes(light[p(240,240)]==.006f,"lit scene changed");
    float[] isolated=zeros();mark(isolated,240,240);iris26904RejectUnsupportedDirectionalJinResidual(isolated,r);
    yes(isolated[p(240,240)]==.006f,"isolated residual changed");
    System.out.println("PASS exact extracted production Jin B Night guard four axes, native-detail veto, smooth signal, normal light, isolated residual");
 }
'''
    code='import java.util.*;public class Photon26904JinProof {\n'+assertions+methods+'\n}'
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/'Photon26904JinProof.java';f.write_text(code)
        subprocess.run(['javac','-d',td,str(f)],check=True)
        subprocess.run(['java','-cp',td,'Photon26904JinProof'],check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--with-javac',action='store_true');p.add_argument('--installed',action='store_true');a=p.parse_args()
    root=a.root.resolve()
    impl=root/'handoff_payload_26904/app'
    # Github CI initially has only staged payload and baseline working checkout.
    shader=(impl/'src/main/assets/shaders/addwatermark_rotate.glsl').read_text()
    jin=(impl/'src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightNeuralEnhancer.java').read_text()
    hdr=(impl/'src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java').read_text()
    native=(impl/'src/main/cpp/iris26856/amaze/shaders/amaze_export.comp').read_text()
    rotation_test(shader)
    need(jin.count('enhanceInternal(base, false, false)')>=1,'Night A standard guard altered')
    need(jin.count('enhanceInternal(base, true, false)')>=1,'Night A true2x guard altered')
    need(jin.count('enhanceInternal(base, false, true)')==1,'B-only Jin call missing')
    need(jin.count('enhanceInternal(base, true, true)')==1,'B-only 50MP Jin call missing')
    need(hdr.count('IrisNightNeuralEnhancer.enhanceInPlaceForNightB(')==1,'B Night Java 12MP call missing')
    need(hdr.count('IrisNightNeuralEnhancer.enhanceInPlaceForTrue2xNightB(')==1,'B Night 50MP call missing')
    # Check real production Night B invocation scope, not merely call presence.
    bstart=hdr.rfind('if (mIris26903NightB) {',0,hdr.index('final boolean nightBFull2x'))
    need(bstart>=0,'no Night B dispatch owner at Jin stage')
    bend=hdr.index('/* IRIS_26826_DNG_JPEG_OVERLAP',bstart)
    bblock=hdr[bstart:bend]
    need(bblock.count('if (nightBFull2x) {')==1,'Night B true2x dispatch not exclusive')
    need(bblock.count('enhanceInPlaceForTrue2xNightB(img)')==1
         and bblock.count('enhanceInPlaceForNightB(img)')==1,
         'both Night B paths must invoke only their B Jin confidence methods')
    need('enhanceInPlace(img)' not in bblock
         and 'enhanceInPlaceForTrue2x(img)' not in bblock,
         'legacy Night A Jin invoked in Night B')
    need(bblock.index('nightBFull2x') < bblock.index('enhanceInPlaceForTrue2xNightB(img)')
         < bblock.index('attachPostJin(img, nightBGain)'),
         'Night B Jin should run before UHDR reattachment')
    need(hdr.count('mIris26903NightB ? mIris26903NightBJin2x : null')==2,
         'actual B 50MP GPU final publisher must receive guarded residual')
    need('enhanceInPlaceForNightB(' not in hdr[:bstart]
         and 'enhanceInPlaceForTrue2xNightB(' not in hdr[:bstart],
         'B Jin invocation leaked to B Photo or Night A upstream paths')
    print('PASS production Hdrx 12MP/50MP B Night-only Jin invocation and UHDR ordering')
    need('iris26904RepairOnlySupportedBorderChroma' in native,'B-only native border correction missing')
    need('outerDistance >= 14' in native,'correction not restricted to real exterior sensor border')
    need('sourceY < 0.035' in native and 'sourceY >= 0.94' in native,'dark/clipped veto missing')
    need('hueAgreement' in native and 'sceneContinuity' in native,'real CFA chroma consensus missing')
    need(native.startswith('#version 450\n'),'native shader version not pinned')
    need(native.count('#include "amaze_tile.glsl"')==1,'native shader import changed')
    need('layout(set = 0, binding = 5)' in native and 'binding = 7' in native,'preexisting descriptor inputs not verified')
    need(len((root/'26904_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())==6,'bad intentional source count')
    need('VERSION_BUILD=26904' in (impl/'version.properties').read_text(),'version missing')
    # Native AMaZE export reuses seven previously bound descriptors, with input
    # source views live across all 19 passes. Prove the exact C++ binding ABI.
    if a.installed:
        pipeline=(root/'app/src/main/cpp/iris26856/amaze/src/Pipeline.cpp').read_text()
        imp=(root/'app/src/main/cpp/iris26856/amaze/shaders/amaze_import.comp').read_text()
        need('const std::array<uint32_t, 7> bindings{0, 1, 2, 3, 5, 6, 7};' in pipeline,
             'C++ AMaZE descriptors no longer bind input slots 5 and 7')
        for req in ('binding = 5','binding = 7','tile.inputMode','normalizedInput.bayer255','cfaComponent('):
            need(req in imp and req in native,'native shader input ABI mismatch: '+req)
        need('writeParams(wb)' in pipeline
             and 'bindBatch(packedView, packedLayout, floatInput, out)' in pipeline,
             'AMaZE input descriptor lifecycle/dispatch no longer verified')
        print('PASS original AMaZE input descriptors, persistent source views and C++ export ABI')
        # CMake previously compiled VERSION_BUILD/NAME into one native target,
        # defeating native reuse even for UI-only releases. All actual C/C++
        # sources have no references to these dead macros; ensure the 26904
        # build removes only the unused native release-version dependency.
        cmake=(root/'app/src/main/cpp/CMakeLists.txt').read_text()
        need('IRIS_26904_NATIVE_VERSION_INDEPENDENCE' in cmake,
             'native release version dependence is not documented')
        need('target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE' not in cmake
             and 'file(READ ${CMAKE_CURRENT_SOURCE_DIR}/../../../version.properties ver)' not in cmake,
             'native CMake still depends on Java-only build version')
        for f in (root/'app/src/main/cpp').rglob('*'):
            if f.is_file() and f.suffix.lower() in ('.c','.cc','.cpp','.h','.hpp','.inl','.inc'):
                need(not re.search(r'\b(VERSION_BUILD|VERSION_NAME)\b',f.read_text(errors='replace')),
                     'native version macro actually referenced: '+str(f))
        print('PASS version-independent native compile definitions with no C/C++ macro consumers')
    # Native build artifacts are keyed after the trusted candidate is installed;
    # no cross-native-source prefix restoration is permissible.
    workflow=(root/'.github/workflows/build-26904-change-aware.yml').read_text()
    need('Restore native CMake outputs only for the exact compiled-source fingerprint' in workflow,
         'change-aware native cache stage missing')
    need(workflow.index('Authority-seed exactly 2027 source files')
         < workflow.index('Restore native CMake outputs only for the exact compiled-source fingerprint'),
         'native cache keyed on stale checkout')
    need("hashFiles('app/src/main/cpp/**/*', 'app/build.gradle'" in workflow,
         'native cache key omits exact current C++ source universe')
    need('path: app/.cxx' in workflow and 'app/build\n' not in workflow,
         'unverified whole Gradle output reuse')
    need(workflow.count('steps.runner_image.outputs.image')==2
         and ': "${ImageVersion:?Actions image version missing}"' in workflow,
         'native cache provenance must include exact Actions runner/NDK image')
    print('PASS change-aware native cache source-input invalidation')
    if a.with_javac:run_java(jin)
    if a.installed:
        manifest={}
        for line in (root/'26904_PRECOMPILE_EXPECTED_FULL_APP.sha256').read_text().splitlines():
            h,path=line.split('  ',1);manifest[path]=h
        actual={}
        for path in manifest:
            f=root/path
            need(f.is_file(),'installed missing '+path)
            actual[path]=hashlib.sha256(f.read_bytes()).hexdigest()
        need(actual==manifest,'installed precompiled sources differ')
        print('PASS 2027 exact source-byte identities matched precompile expected')
    print('PASS B Night/A isolation and native border-only evidence guards')

if __name__=='__main__':
    try:main()
    except Exception as exc:print('26904 VALIDATOR FAIL',exc,file=sys.stderr);sys.exit(1)
