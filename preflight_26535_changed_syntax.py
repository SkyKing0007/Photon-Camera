#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, tempfile, shutil
from pathlib import Path
JAVA=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2MgcSourceExposure.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2HighlightChromaReliability.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2Jpeg444Encoder.java',
]
KOTLIN='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt'
PARSER=r'''import java.util.*; import javax.tools.*; import com.sun.source.util.*; public class ParseJava26535 { public static void main(String[] a)throws Exception{ JavaCompiler c=ToolProvider.getSystemJavaCompiler(); if(c==null)throw new RuntimeException("javac unavailable"); DiagnosticCollector<JavaFileObject>d=new DiagnosticCollector<>(); StandardJavaFileManager fm=c.getStandardFileManager(d,null,null); Iterable<? extends JavaFileObject>f=fm.getJavaFileObjectsFromStrings(Arrays.asList(a)); JavacTask t=(JavacTask)c.getTask(null,fm,d,Arrays.asList("-proc:none"),null,f); t.parse(); boolean bad=false; for(Diagnostic<?>x:d.getDiagnostics())if(x.getKind()==Diagnostic.Kind.ERROR){System.err.println(x);bad=true;} fm.close(); if(bad)System.exit(2); }}'''
def fail(m): raise SystemExit('FAIL: '+m)
def req(c,m):
    if not c: fail(m)
def strip_kotlin(s):
    out=[];i=0;n=len(s);mode='code';quote=''
    while i<n:
        ch=s[i];nx=s[i+1] if i+1<n else ''
        if mode=='code':
            if ch=='/' and nx=='/': out.extend('  ');i+=2;mode='line';continue
            if ch=='/' and nx=='*': out.extend('  ');i+=2;mode='block';continue
            if s.startswith('"""',i): out.extend('   ');i+=3;mode='triple';continue
            if ch in ('"',"'"): quote=ch;out.append(' ');i+=1;mode='string';continue
            out.append(ch);i+=1;continue
        if mode=='line': out.append('\n' if ch=='\n' else ' '); i+=1; mode='code' if ch=='\n' else mode; continue
        if mode=='block':
            if ch=='*' and nx=='/': out.extend('  ');i+=2;mode='code'
            else: out.append('\n' if ch=='\n' else ' ');i+=1
            continue
        if mode=='triple':
            if s.startswith('"""',i): out.extend('   ');i+=3;mode='code'
            else: out.append('\n' if ch=='\n' else ' ');i+=1
            continue
        if mode=='string':
            if ch=='\\': out.extend('  ' if i+1<n else ' ');i+=2;continue
            if ch==quote: out.append(' ');i+=1;mode='code';continue
            out.append('\n' if ch=='\n' else ' ');i+=1
    req(mode in ('code','line'),'Kotlin unterminated lexical mode '+mode); return ''.join(out)
def balance(s):
    clean=strip_kotlin(s);stack=[];pairs={')':'(',']':'[','}':'{'}
    for ln,line in enumerate(clean.splitlines(),1):
        for col,ch in enumerate(line,1):
            if ch in '([{': stack.append((ch,ln,col))
            elif ch in ')]}': req(stack and stack[-1][0]==pairs[ch],f'Kotlin delimiter mismatch {ch} at {ln}:{col}'); stack.pop()
    req(not stack,'Kotlin unclosed delimiter '+repr(stack[-1] if stack else None))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
    paths=[]
    for rel in JAVA: p=root/rel;req(p.is_file(),'missing '+rel);paths.append(str(p))
    kp=root/KOTLIN;req(kp.is_file(),'missing '+KOTLIN)
    with tempfile.TemporaryDirectory(prefix='iris26535-java-') as td:
        td=Path(td);src=td/'ParseJava26535.java';src.write_text(PARSER)
        cp=subprocess.run(['javac','-d',str(td),str(src)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);req(cp.returncode==0,'parser helper compile\n'+cp.stdout)
        cp=subprocess.run(['java','-cp',str(td),'ParseJava26535',*paths],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);req(cp.returncode==0,'changed Java parse\n'+cp.stdout)
    ks=kp.read_text();balance(ks)
    for t in ('java.io.RandomAccessFile','IRIS_26535_NATIVE_SPATIAL_RELIABILITY','IRIS_26535_SR_RELIABILITY_GATE','grid8x6='):
        req(t in ks,'Kotlin contract missing '+t)
    kotlinc=shutil.which('kotlinc')
    if kotlinc:
        with tempfile.TemporaryDirectory(prefix='iris26535-kotlin-') as td:
            cp=subprocess.run([kotlinc,str(kp),'-d',str(Path(td)/'out.jar')],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            grammar=[x for x in cp.stdout.splitlines() if any(y in x.lower() for y in ('expecting ','syntax error','unexpected tokens','unclosed comment'))]
            req(not grammar,'Kotlin grammar diagnostics\n'+'\n'.join(grammar))
    print('PASS: 26535 javac parser accepted 6 changed/new Java files')
    print('PASS: 26535 Kotlin bridge lexical/grammar preflight accepted')
if __name__=='__main__': main()
