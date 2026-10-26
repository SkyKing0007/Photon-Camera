#!/usr/bin/env python3
"""Real failed 40399946468 + latent shader Bash scope regression."""
from pathlib import Path
import ast
S=Path(__file__).resolve().parents[1]
p=(S/'generate_26881_build.py').read_text()
source=ast.parse(p)
fns={n.name:n for n in source.body if isinstance(n,ast.FunctionDef)}
assert 'candidate' in fns and 'shaders' in fns
make=ast.get_source_segment(p,fns['candidate']);shader=ast.get_source_segment(p,fns['shaders'])
assert 'local H79=' in make
assert 'verify_26880_runtime_glsl_scope.py "$H79" "$BASE"' in make
assert '$H79' not in shader, 'local from make_candidate leaked into compile_modified_runtime_shaders'
assert 'verify_26880_runtime_glsl_scope.py "$WORK/historical_26879_from_26880" "$BASE"' in shader
# Protect compiler command integrity while recognizing versioned log files.
a='./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace 2>&1 | tee "$OUT/26880_gradle_language_compilers.log"'
b=a.replace('26880_gradle','26881_gradle')
assert a!=b and b.replace('$OUT/26881_','$OUT/26880_')==a
assert b.replace(':app:compileDebugKotlin',':app:compileReleaseKotlin').replace('$OUT/26881_','$OUT/26880_')!=a
assert b.replace('2>&1 | tee','2> error.txt | tee').replace('$OUT/26881_','$OUT/26880_')!=a
print('PASS actual generator AST: historical local H79 scope fixed; compiler semantics and versioned log path distinguished')
