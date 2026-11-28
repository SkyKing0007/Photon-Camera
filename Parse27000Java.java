import javax.tools.*;
import com.sun.source.util.JavacTask;
import java.util.*;
public class Parse27000Java {
 public static void main(String[] args) throws Exception {
  JavaCompiler c=ToolProvider.getSystemJavaCompiler();DiagnosticCollector<JavaFileObject> diagnostics=new DiagnosticCollector<>();
  try(StandardJavaFileManager m=c.getStandardFileManager(diagnostics,null,null)){
   JavacTask t=(JavacTask)c.getTask(null,m,diagnostics,List.of("-proc:none"),null,m.getJavaFileObjectsFromStrings(Arrays.asList(args)));for(var u:t.parse()){}
   int n=0;for(var d:diagnostics.getDiagnostics())if(d.getKind()==Diagnostic.Kind.ERROR){System.err.println(d);n++;}if(n>0)throw new IllegalStateException(n+" Java syntax errors");
   System.out.println("PASS javac syntax "+args.length+" files");
  }
 }
}
