import com.sun.source.util.JavacTask;
import java.io.File;
import java.util.Arrays;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

/** Parse the actual modified Java compilation units with JDK 17; Android
 * symbol resolution is intentionally delegated to full Gradle Java compile. */
public final class SourceGrammar26914 {
    public static void main(String[] paths) throws Exception {
        if (paths.length != 6) throw new AssertionError("26913 missing production Java sources");
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new AssertionError("JDK compiler unavailable");
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager files = compiler.getStandardFileManager(diagnostics, null, null)) {
            var units = files.getJavaFileObjectsFromFiles(Arrays.stream(paths).map(File::new).toList());
            JavacTask task = (JavacTask) compiler.getTask(null, files, diagnostics,
                    Arrays.asList("-proc:none", "--release", "17"), null, units);
            int parsed = 0;
            for (var unit : task.parse()) {
                if (unit == null) throw new AssertionError("missing parsed unit");
                parsed++;
            }
            if (!diagnostics.getDiagnostics().isEmpty() || parsed != paths.length)
                throw new AssertionError("26914 production Java grammar failed: " + diagnostics.getDiagnostics());
            System.out.println("PASS 26913 real Java grammar parsed=" + parsed);
        }
    }
}
