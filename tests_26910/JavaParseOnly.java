import java.util.*;
import javax.tools.*;
import com.sun.source.util.JavacTask;
/** Parse real production Java without requiring an Android SDK on the packaging host. */
public final class JavaParseOnly {
 public static void main(String[] args) throws Exception {
  JavaCompiler compiler=ToolProvider.getSystemJavaCompiler();
  if(compiler==null)throw new AssertionError("JDK compiler missing");
  DiagnosticCollector<JavaFileObject> diagnostics=new DiagnosticCollector<>();
  try(StandardJavaFileManager fm=compiler.getStandardFileManager(diagnostics,null,null)) {
   var files=fm.getJavaFileObjectsFromStrings(Arrays.asList(args));
   var task=(JavacTask)compiler.getTask(null,fm,diagnostics,List.of("-proc:none"),null,files);
   int n=0; for(var ignored:task.parse())n++;
   for(var d:diagnostics.getDiagnostics()) if(d.getKind()==Diagnostic.Kind.ERROR)
    throw new AssertionError("Syntax error "+d.toString());
   if(n!=args.length)throw new AssertionError("Incomplete Java source parse");
   System.out.println("PASS 26909 actual javac grammar parse all "+n+" edited production sources");
  }
 }
}
