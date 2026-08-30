#!/usr/bin/env python3
from pathlib import Path
import argparse, ast, hashlib, math, sys

CHANGED=[
'app/src/main/cpp/motionv2_jpeg444_jni.cpp',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/UltraHdrSaver.java',
'app/version.properties',
]
PASS=[]
def ok(name,cond):
    if not cond: raise SystemExit('FAIL '+name)
    PASS.append(name); print('PASS',name)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def text(root,rel): return (Path(root)/rel).read_text()
def exact_once(s,needle): return s.count(needle)==1

def parse_manifest(p):
    # REGRESSION_26564_V1_HANDOFF_SCOPE_NEWLINE: splitlines strips line endings.
    rows=[]
    for line in Path(p).read_text().splitlines():
        if not line.strip(): continue
        h,rel=line.split('  ',1); rows.append((h,rel))
    return rows

def verify_manifest(root,p,expected_count=None):
    rows=parse_manifest(p)
    if expected_count is not None: ok(Path(p).name+' line count',len(rows)==expected_count)
    for h,rel in rows:
        q=Path(root)/rel
        ok('manifest '+rel,q.is_file() and sha(q)==h)
    return rows

def dng_region(p):
    s=Path(p).read_text(); a=s.index('        public static boolean saveStackedRaw('); b=s.index('\n    }\n}',a)
    return s[a:b].encode()

def srgb_decode(x): return x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4
def srgb_encode(x):
    x=max(0.0,min(1.0,x)); return 12.92*x if x<=0.0031308 else 1.055*(x**(1/2.4))-0.055
def p3(r,g,b):
    r,g,b=map(srgb_decode,(r,g,b))
    pr=0.8224619687*r+0.1775380313*g
    pg=0.0331941989*r+0.9668058011*g
    pb=0.0170826307*r+0.0723974407*g+0.9105199286*b
    return tuple(map(srgb_encode,(pr,pg,pb)))

def validate(root,base=None,package=None):
    root=Path(root); package=Path(package) if package else Path(__file__).resolve().parent
    v=text(root,'app/version.properties'); ok('target version','VERSION_NAME=0.9726565\n' in v and 'VERSION_BUILD=26565\n' in v and 'VERSION_NAME=0.9726564' not in v and 'VERSION_BUILD=26564' not in v)
    ok('changed-path inventory exact', (package/'V1_26565_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines()==CHANGED)

    cpp=text(root,CHANGED[0]); img=text(root,CHANGED[1]); bridge=text(root,CHANGED[2]); enc=text(root,CHANGED[3]); uh=text(root,CHANGED[4])
    ok('Display-P3 boundary owner marker',exact_once(cpp,'IRIS_26565_JPEG_BOUNDARY_DISPLAY_P3'))
    ok('P3 matrix exact',all(x in cpp for x in ('0.8224619687f','0.1775380313f','0.0331941989f','0.9668058011f','0.0170826307f','0.0723974407f','0.9105199286f')))
    ok('P3 ICC generated from pinned UltraHDR', 'IccHelper::writeIccProfile(UHDR_CT_SRGB,UHDR_CG_DISPLAY_P3)' in cpp and 'jpeg_write_icc_profile' in cpp)
    ok('true2x conversion follows Jin', 'applyJinPixel(j,c,r,d,left+x,top+y,outW,outH,&row[(size_t)x*3]);p3.convertInPlace(&row[(size_t)x*3])' in cpp)
    ok('true2x JPEG embeds P3 ICC', 'jpeg_start_compress(&c,TRUE);bool ok=writeDisplayP3Icc(&c);' in cpp)
    ok('native bitmap P3 copy does not mutate source', 'out = source.copy(Bitmap.Config.ARGB_8888, true);' in enc and 'convertSrgbToDisplayP3Native(out)' in enc)
    ok('Android P3 fallback guarded API26', 'Build.VERSION.SDK_INT < 26' in enc and 'ColorSpace.Named.DISPLAY_P3' in enc)
    ok('JPEG-R packages Display-P3 gamut', 'packageJpegRNative(base.toString(),gain.toString(),output.toString(),1,' in enc and 'packageJpegRNative(base.toString(), gain.toString(), output.toString(), 1,' in enc)
    ok('normal UHDR computes gain before P3 copy', uh.index('gainmapBitmap = createGainmapBitmap(bitmap') < uh.index('outputBitmap = MotionV2Jpeg444Encoder.toDisplayP3BitmapCopy(bitmap)'))
    ok('normal JPEG publication P3 native-first', 'MotionV2Jpeg444Encoder.write(fileToSave, img, jpgQuality)' in img and 'compressDisplayP3AndroidFallback(fileToSave, img, jpgQuality)' in img)
    ok('Night portable JPEG is P3', 'IRIS_26565_NIGHT_PLAIN_DISPLAY_P3_JPEG_FAILED' in img and 'IRIS_26565_NIGHT_ANDROID_P3_JPEG_RESULT' in img)
    ok('Night true2x failure preserves checkpoint', 'IRIS_26565_NIGHT_TRUE2X_FINAL_FAILED checkpointPreserved=true nativeReplacement=false' in img and 'IRIS_26564_NIGHT_TRUE2X_CODEC_FALLBACK baseResolution=true' not in img)
    ok('true2x luma-zero skips redundant fullres MGC', 'val runTrue2xFullResolutionMgc = runFullResolutionDenoise && lumaScale > 0f' in bridge and 'runDenoise = runTrue2xFullResolutionMgc' in bridge)
    ok('native residual guidance retained', 'nativeResidualDenoise=$runFullResolutionDenoise' in bridge and 'vgnGuideConsumed=true' in bridge)
    ok('50MP SDR retained on UHDR packaging failure', 'IRIS_26565_TRUE2X_UHDR_FALLBACK_50MP_SDR' in enc and 'Files.move(base, output, java.nio.file.StandardCopyOption.REPLACE_EXISTING)' in enc and 'native12mpFallback=false' in enc)

    # Numeric sanity: neutral axis preserved; conversion is not mere retagging; bounded values.
    for v in (0.0,0.18,0.5,1.0):
        q=p3(v,v,v); ok(f'P3 neutral {v}',max(q)-min(q)<2e-9 and all(-1e-12<=x<=1+1e-12 for x in q))
    red=p3(1,0,0); ok('P3 numeric changes sRGB red',abs(red[0]-1)>1e-3 and red[1]>0 and red[2]>0)

    # 26564 Kotlin nullable-Throwable regression must remain fixed.
    kg=text(root,'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt')
    ok('26564 nullable Throwable regression retained', 'val gpuFailure = gpuAttempt.exceptionOrNull()' in kg and '?: IllegalStateException("IRIS_26564_TRUE2X_GPU_FALLBACK_CPU unknown GPU failure")' in kg and 'gpuFailure,' in kg)

    if base:
        base=Path(base)
        # Complete changed scope by full app file hashes.
        def tree(r):
            d={}
            for p in (Path(r)/'app').rglob('*'):
                if p.is_file(): d[p.relative_to(r).as_posix()]=sha(p)
            return d
        a,b=tree(base),tree(root); diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
        ok('exact six-file runtime scope',diff==CHANGED)
        # Protected full files.
        for h,rel in parse_manifest(package/'V1_26565_PROTECTED_UNCHANGED_CORE.sha256'):
            ok('protected base hash '+rel,sha(base/rel)==h)
            ok('protected candidate hash '+rel,sha(root/rel)==h)
        # Edited ImageSaver DNG region exact bytes.
        bd=dng_region(base/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
        cd=dng_region(root/'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java')
        want=parse_manifest(package/'V1_26565_DNG_REGION.sha256')[0][0]
        ok('ImageSaver DNG region byte invariant',bd==cd and hashlib.sha256(cd).hexdigest()==want)

    print(f'PASS TOTAL {len(PASS)} / {len(PASS)}')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('candidate'); ap.add_argument('--base'); ap.add_argument('--package')
    a=ap.parse_args(); validate(a.candidate,a.base,a.package)
