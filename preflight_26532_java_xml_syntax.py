#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, tempfile, xml.etree.ElementTree as ET
from pathlib import Path

JAVA = [x.strip() for x in '''
app/src/main/java/com/particlesdevs/photoncamera/control/IrisZoomController.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ImageSaver.java
app/src/main/java/com/particlesdevs/photoncamera/processing/IrisMotionSuperResDngWriter.java
app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java
app/src/main/java/com/particlesdevs/photoncamera/processing/processor/MotionV2Merger.java
app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java
app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java
app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java
app/src/main/java/com/particlesdevs/photoncamera/settings/SettingType.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraActivity.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIController.java
app/src/main/java/com/particlesdevs/photoncamera/ui/camera/viewmodel/SettingsBarEntryProvider.java
'''.splitlines() if x.strip()]
XML = ['app/src/main/res/values/ids.xml','app/src/main/res/values/strings.xml']
PARSER = r'''
import java.io.*; import java.util.*; import javax.tools.*; import com.sun.source.util.*;
public class ParseJava26532 {
  public static void main(String[] a) throws Exception {
    JavaCompiler c=ToolProvider.getSystemJavaCompiler(); if(c==null) throw new RuntimeException("javac unavailable");
    DiagnosticCollector<JavaFileObject> d=new DiagnosticCollector<>();
    StandardJavaFileManager fm=c.getStandardFileManager(d,null,null);
    Iterable<? extends JavaFileObject> f=fm.getJavaFileObjectsFromStrings(Arrays.asList(a));
    JavacTask t=(JavacTask)c.getTask(null,fm,d,Arrays.asList("-proc:none"),null,f); t.parse();
    boolean bad=false; for(Diagnostic<?> x:d.getDiagnostics()) if(x.getKind()==Diagnostic.Kind.ERROR){System.err.println(x); bad=true;}
    fm.close(); if(bad) System.exit(2);
  }
}
'''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root)
    paths=[]
    for rel in JAVA:
        p=root/rel
        if not p.is_file(): raise SystemExit('FAIL: missing '+rel)
        paths.append(str(p))
    for rel in XML:
        p=root/rel
        if not p.is_file(): raise SystemExit('FAIL: missing '+rel)
        ET.parse(p)
    with tempfile.TemporaryDirectory(prefix='iris26532-java-parse-') as td:
        td=Path(td); src=td/'ParseJava26532.java'; src.write_text(PARSER)
        cp=subprocess.run(['javac','-d',str(td),str(src)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if cp.returncode: print(cp.stdout); raise SystemExit('FAIL: Java parser helper compile')
        cp=subprocess.run(['java','-cp',str(td),'ParseJava26532',*paths],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        if cp.returncode: print(cp.stdout); raise SystemExit('FAIL: changed Java syntax parse')
    print(f'PASS: 26532 Java parser accepted {len(JAVA)} changed Java files')
    print(f'PASS: 26532 XML parser accepted {len(XML)} changed resource files')
if __name__=='__main__': main()
