#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, tempfile, shutil, re
from pathlib import Path

JAVA=[
'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/ImageFrame.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/SaverImplementation.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/IrisRcdBayerInput.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/PostPipeline.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
]
KOTLIN='app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisNightMgc1271Bridge.kt'
PARSER=r'''
import java.util.*; import javax.tools.*; import com.sun.source.util.*;
public class ParseJava26533V16 {
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

def fail(msg): raise SystemExit('FAIL: '+msg)
def require(c,msg):
    if not c: fail(msg)

def strip_kotlin(s:str)->str:
    # Preserve delimiters/newlines while neutralizing strings and comments for a deterministic balance check.
    out=[]; i=0; n=len(s); mode='code'; quote=''
    while i<n:
        ch=s[i]; nx=s[i+1] if i+1<n else ''
        if mode=='code':
            if ch=='/' and nx=='/': out.extend('  '); i+=2; mode='line'; continue
            if ch=='/' and nx=='*': out.extend('  '); i+=2; mode='block'; continue
            if s.startswith('"""',i): out.extend('   '); i+=3; mode='triple'; continue
            if ch in ('"',"'"): quote=ch; out.append(' '); i+=1; mode='string'; continue
            out.append(ch); i+=1; continue
        if mode=='line':
            if ch=='\n': out.append('\n'); mode='code'
            else: out.append(' ')
            i+=1; continue
        if mode=='block':
            if ch=='*' and nx=='/': out.extend('  '); i+=2; mode='code'
            else: out.append('\n' if ch=='\n' else ' '); i+=1
            continue
        if mode=='triple':
            if s.startswith('"""',i): out.extend('   '); i+=3; mode='code'
            else: out.append('\n' if ch=='\n' else ' '); i+=1
            continue
        if mode=='string':
            if ch=='\\': out.extend('  ' if i+1<n else ' '); i+=2; continue
            if ch==quote: out.append(' '); i+=1; mode='code'; continue
            out.append('\n' if ch=='\n' else ' '); i+=1
    require(mode in ('code','line'), f'Kotlin unterminated lexical construct mode={mode}')
    return ''.join(out)

def kotlin_balance(s:str):
    clean=strip_kotlin(s); stack=[]; pairs={')':'(',']':'[','}':'{'}
    for ln,line in enumerate(clean.splitlines(),1):
        for col,ch in enumerate(line,1):
            if ch in '([{': stack.append((ch,ln,col))
            elif ch in ')]}':
                require(stack and stack[-1][0]==pairs[ch], f'Kotlin delimiter mismatch {ch} at {ln}:{col}')
                stack.pop()
    require(not stack, f'Kotlin unclosed delimiter {stack[-1] if stack else None}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root)
    paths=[]
    for rel in JAVA:
        p=root/rel; require(p.is_file(),'missing '+rel); paths.append(str(p))
    kp=root/KOTLIN; require(kp.is_file(),'missing '+KOTLIN)
    with tempfile.TemporaryDirectory(prefix='iris26533-v16-java-parse-') as td:
        td=Path(td); src=td/'ParseJava26533V16.java'; src.write_text(PARSER)
        cp=subprocess.run(['javac','-d',str(td),str(src)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        require(cp.returncode==0,'Java parser helper compile:\n'+cp.stdout)
        cp=subprocess.run(['java','-cp',str(td),'ParseJava26533V16',*paths],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        require(cp.returncode==0,'changed Java syntax parse:\n'+cp.stdout)
    kotlin_balance(kp.read_text(encoding='utf-8'))
    # Also ask kotlinc to parse/type-analyze the changed bridge when available. Missing Android/project
    # symbols are expected in isolation; grammar diagnostics are not.
    kotlinc=shutil.which('kotlinc')
    if kotlinc:
        with tempfile.TemporaryDirectory(prefix='iris26533-v16-kotlin-parse-') as td:
            cp=subprocess.run([kotlinc,str(kp),'-d',str(Path(td)/'out.jar')],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            grammar=[]
            for line in cp.stdout.splitlines():
                low=line.lower()
                if ('expecting ' in low or 'syntax error' in low or 'unexpected tokens' in low or
                    'unclosed comment' in low or 'missing ' in low and '}' in low): grammar.append(line)
            require(not grammar,'Kotlin grammar diagnostics:\n'+'\n'.join(grammar))
    print(f'PASS: V1.6 javac parser accepted {len(JAVA)} changed Java files')
    print('PASS: V1.6 Kotlin bridge lexical/grammar preflight accepted')

if __name__=='__main__': main()
