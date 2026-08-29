#!/usr/bin/env python3
from pathlib import Path
import argparse, shutil, struct, subprocess, tempfile

def parse_ifd(data: bytes):
    assert data[:2] == b'II' and struct.unpack_from('<H',data,2)[0] == 42
    off=struct.unpack_from('<I',data,4)[0]
    n=struct.unpack_from('<H',data,off)[0]
    out={}
    p=off+2
    for _ in range(n):
        tag,typ,count,val=struct.unpack_from('<HHII',data,p); p+=12
        out[tag]=(typ,count,val)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidate',type=Path,required=True); a=ap.parse_args()
    javac=shutil.which('javac'); java=shutil.which('java')
    if not javac or not java: raise SystemExit('javac/java required for DNG serializer self-test')
    writer=a.candidate/'app/src/main/java/com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java'
    if not writer.is_file(): raise SystemExit('Sabre DNG writer missing')
    with tempfile.TemporaryDirectory(prefix='iris26562_dng_') as td:
        root=Path(td); src=root/'src'; cls=root/'classes'; cls.mkdir()
        def w(rel,text):
            p=src/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
        w('android/os/Build.java','package android.os; public final class Build { public static String BRAND="TestBrand", MANUFACTURER="TestMaker", MODEL="TestModel"; }')
        w('com/particlesdevs/photoncamera/util/Log.java','package com.particlesdevs.photoncamera.util; public final class Log { public static void i(String t,String m){} public static void e(String t,String m,Throwable x){x.printStackTrace();} }')
        w('com/particlesdevs/photoncamera/processing/render/Parameters.java','''package com.particlesdevs.photoncamera.processing.render;
public class Parameters {
 public boolean irisNightActive=false; public float motionV2GlobalZoom=1f, motionV2RenderResidualZoom=1f;
 public int cameraRotation=0, iso=100, calibrationIlluminant1=21, calibrationIlluminant2=17;
 public double exposureTime=0.01; public float aperture=1.8f,focalLength=8.0f;
 public float[] ColorMatrix1={1,0,0,0,1,0,0,0,1},ColorMatrix2={1,0,0,0,1,0,0,0,1},calibrationTransform1={1,0,0,0,1,0,0,0,1},calibrationTransform2={1,0,0,0,1,0,0,0,1},ForwardTransform1={1,0,0,0,1,0,0,0,1},ForwardTransform2={1,0,0,0,1,0,0,0,1},whitePoint={1,1,1};
}''')
        target=src/'com/particlesdevs/photoncamera/processing/IrisSabreSuperResDngWriter.java'; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(writer,target)
        w('TestMain.java','''import java.nio.file.*; import com.particlesdevs.photoncamera.processing.IrisSabreSuperResDngWriter; import com.particlesdevs.photoncamera.processing.render.Parameters;
public class TestMain { public static void main(String[] a)throws Exception { Path rgb=Paths.get(a[0]), dng=Paths.get(a[1]); byte[] p=new byte[4*2*6]; for(int i=0;i<p.length;i++)p[i]=(byte)i; Files.write(rgb,p); if(!IrisSabreSuperResDngWriter.write(dng,rgb,4,2,new Parameters(),3,1,1,1,2,2,3,2)) throw new RuntimeException("write failed"); }}''')
        files=[str(p) for p in src.rglob('*.java')]
        subprocess.run([javac,'-d',str(cls),*files],check=True)
        rgb=root/'test.rgb16'; dng=root/'test.dng'
        subprocess.run([java,'-cp',str(cls),'TestMain',str(rgb),str(dng)],check=True)
        data=dng.read_bytes(); tags=parse_ifd(data)
        def scalar(tag):
            typ,count,val=tags[tag]; assert count==1; return val & (0xffff if typ==3 else 0xffffffff)
        assert scalar(256)==4 and scalar(257)==2
        assert scalar(262)==34892 and scalar(277)==3
        assert scalar(279)==48
        assert 51041 not in tags, 'Bayer NoiseProfile tag leaked into LinearRaw DNG'
        typ,count,off=tags[258]; assert typ==3 and count==3
        bits=struct.unpack_from('<HHH',data,off); assert bits==(16,16,16)
        assert b'Spatial' not in data and b'Sabre Super Res LinearRaw' in data
    print('PASS 26562 Sabre LinearRaw DNG serializer self-test: RGB16 3-channel 2x geometry, no Bayer NoiseProfile, no Spatial provenance')
if __name__=='__main__': main()
