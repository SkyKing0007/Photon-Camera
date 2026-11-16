#!/usr/bin/env python3
"""26943 strict active Java/Kotlin/native routes and Java full-file AST scope check.
The original pinned real Android Kotlin/Java/NDK/GLSL/assemble gates remain mandatory.
"""
import sys, re, subprocess, tempfile
from pathlib import Path
from build_26943_incremental import R, scope, fail
PATH={
'capture':'app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java',
'native':'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26864NativeRawr.java',
'bridge':'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'jpeg':'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/HdrxProcessor.java',
'jni':'app/src/main/cpp/iris26864/Iris26864JniGpuInteropImpl.inc',
'runner':'app/src/main/cpp/iris26864/Iris26864FrozenDirectRawrRunner.cpp',
}
AST=r'''import java.util.*;
import javax.tools.*;
import com.sun.source.tree.*;
import com.sun.source.util.*;
public final class Photon26943JavaScopeCheck {
    public static void main(String[] args) throws Exception {
        if(args.length!=1)throw new IllegalArgumentException("expected real HdrxProcessor.java path");
        JavaCompiler compiler=ToolProvider.getSystemJavaCompiler();
        if(compiler==null)throw new IllegalStateException("JDK javac missing");
        DiagnosticCollector<JavaFileObject> diags=new DiagnosticCollector<>();
        try(StandardJavaFileManager fm=compiler.getStandardFileManager(diags,null,null)) {
            JavacTask task=(JavacTask)compiler.getTask(null,fm,diags,List.of("-proc:none"),null,
                fm.getJavaFileObjectsFromStrings(List.of(args[0])));
            final int[] hits={0};
            for(CompilationUnitTree root:task.parse()) {
                new TreePathScanner<Void,Void>() {
                    private Deque<Set<String>> names;
                    @Override public Void visitMethod(MethodTree method,Void arg) {
                        if(!method.getName().contentEquals("ApplyHdrX"))return super.visitMethod(method,arg);
                        if(names!=null)throw new IllegalStateException("unexpected nested method");
                        names=new ArrayDeque<>();names.push(new HashSet<>());
                        try{return super.visitMethod(method,arg);}finally{names.pop();names=null;}
                    }
                    @Override public Void visitBlock(BlockTree block,Void arg) {
                        if(names==null)return super.visitBlock(block,arg);
                        names.push(new HashSet<>());
                        try{return super.visitBlock(block,arg);}finally{names.pop();}
                    }
                    @Override public Void visitVariable(VariableTree var,Void arg) {
                        if(names!=null)names.peek().add(var.getName().toString());
                        return super.visitVariable(var,arg);
                    }
                    @Override public Void visitMethodInvocation(MethodInvocationTree call,Void arg) {
                        if(names!=null&&call.getMethodSelect().toString().endsWith("GlesIris26864NativeRawr.takeTiming")) {
                            hits[0]++;
                            if(call.getArguments().size()!=1||!(call.getArguments().get(0) instanceof IdentifierTree))
                                throw new IllegalStateException("nonlocal or structurally invalid timing argument");
                            String name=((IdentifierTree)call.getArguments().get(0)).getName().toString();
                            if(!name.equals("iris26363ReferenceTimestamp"))
                                throw new IllegalStateException("wrong original shutter-owned reference timestamp: "+name);
                            if(names.stream().noneMatch(scope->scope.contains(name)))
                                throw new IllegalStateException("Java lexical scope violation for "+name);
                        }
                        return super.visitMethodInvocation(call,arg);
                    }
                }.scan(root,null);
            }
            for(Diagnostic<? extends JavaFileObject> d:diags.getDiagnostics())
                if(d.getKind()==Diagnostic.Kind.ERROR)throw new IllegalStateException("Java parse error "+d);
            if(hits[0]!=1)throw new IllegalStateException("expected exactly one current timing EXIF consumer, got "+hits[0]);
        }
        System.out.println("PASS full HdrxProcessor.java JDK AST Java lexical scope and exact original reference timestamp");
    }
}
'''
def check_java_actual_source(java_text):
    # The timestamp is the identical token passed into the B RAW reconstruction;
    # recordTiming(referenceTimestamp) in the bridge must use the same key.
    if java_text.count('long iris26363ReferenceTimestamp = Long.MIN_VALUE;')!=1:
        fail('missing original outer-method shutter timestamp declaration')
    if java_text.count('                            iris26363ReferenceTimestamp,')!=1:
        fail('RAW reconstruction missing original shutter timestamp parameter')
    if java_text.count('GlesIris26864NativeRawr.takeTiming(\n                            iris26363ReferenceTimestamp)')!=1:
        fail('EXIF timing must consume original declared shutter timestamp, not branch-local result')
    with tempfile.TemporaryDirectory(prefix='photon26943_java_scope_') as td:
        tmp=Path(td)
        cls=tmp/'Photon26943JavaScopeCheck.java';cls.write_text(AST)
        yes=tmp/'HdrxProcessor.java';yes.write_text(java_text)
        r=subprocess.run(['javac','-encoding','UTF-8','-d',str(tmp),str(cls)],capture_output=True,text=True)
        if r.returncode:fail('real JDK AST fixture compilation failed '+r.stderr[-900:])
        check=['java','-cp',str(tmp),'Photon26943JavaScopeCheck',str(yes)]
        r=subprocess.run(check,capture_output=True,text=True)
        if r.returncode:fail('actual complete Java syntax/lexical scope failed '+r.stderr[-900:])
        # Negative reintroduces EXACT V3 failure, and must be caught before Actions Gradle.
        bad=java_text.replace('GlesIris26864NativeRawr.takeTiming(\n                            iris26363ReferenceTimestamp)',
                              'GlesIris26864NativeRawr.takeTiming(\n                            iris26409V2.referenceTimestamp)')
        yes.write_text(bad)
        r=subprocess.run(check,capture_output=True,text=True)
        if r.returncode==0:fail('V3 compile failure was not rejected by real Java AST scope regression')
        if 'nonlocal or structurally invalid timing argument' not in r.stderr:
            fail('V3 failure did not trigger intended Java scope negative '+r.stderr[-500:])
        # Negative another newly made-up identifier (still a syntactically valid argument)
        bad=java_text.replace('GlesIris26864NativeRawr.takeTiming(\n                            iris26363ReferenceTimestamp)',
                              'GlesIris26864NativeRawr.takeTiming(\n                            missingTimeKey)')
        yes.write_text(bad)
        r=subprocess.run(check,capture_output=True,text=True)
        if r.returncode==0:fail('unknown timing identifier accepted by Java AST scope regression')
    print('PASS real JDK Java full-file AST scope and exact historical V3 compile-failure negative')
def main():
    scope();live='--live' in sys.argv
    texts={k:(R/path if live else R/'handoff_payload_26943'/path).read_text() for k,path in PATH.items()}
    def expect(k,marks):
        for m in marks:
            if m not in texts[k]:fail('missing Java/native cross-reference '+k+': '+m)
    expect('capture',('iris26943StageOptionalGpuZsl(img);','SDK_INT < 33','img.getHardwareBuffer()','img.getFence()',
        'fence.getSignalTime()','SIGNAL_TIME_PENDING','SIGNAL_TIME_INVALID',
        'zoom.outputLocalZoom >= 1.10f','!iris26871BExposureSelected()','PreferenceKeys.isIrisSuperResOn()',
        'mIris26548CameraHealthGeneration','tryZslGpuStage(','buffer.close();'))
    if 'getFdDup()' in texts['capture'] or 'getFd(' in texts['capture']:fail('Android public SyncFence FD API invalid')
    expect('native',('nativeTryZslGpuStage','nativeTakeLastTimings','recordTiming(','takeTiming('))
    expect('jni',('Java_com_hinnka_mycamera_processor_GlesIris26864NativeRawr_nativeTryZslGpuStage','AHardwareBuffer_acquire','std::try_to_lock'))
    expect('bridge',('recordTiming(referenceTimestamp)','GlesIris26864NativeRawr.run('))
    expect('jpeg',('Iris Photo B HDR+ Higher Quality','GlesIris26864NativeRawr.takeTiming','exifData.IMAGE_DESCRIPTION','iris26943Timing'))
    expect('runner',('Java_com_hinnka_mycamera_processor_GlesIris26864NativeRawr_nativeTakeLastTimings','iris26943LastTimings.clear()'))
    check_java_actual_source(texts['jpeg'])
    print('PASS 26943 original Java/Kotlin/C++ routes, API33 AHB/SyncFence and real JDK full-file EXIF scope regression')
if __name__=='__main__':
    try:main()
    except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
