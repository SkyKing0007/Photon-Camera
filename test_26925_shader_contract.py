#!/usr/bin/env python3
"""26925 GLSL/Kotlin source/ABI/versions/static preflights, compiler still mandatory."""
from pathlib import Path
import sys,re,subprocess,textwrap
R=Path(__file__).resolve().parent
P=R/'handoff_payload_26925' if '--payload' in sys.argv else R
J=P/'app/src/main/java/com/hinnka/mycamera/processor'
B=P/'app/src/main/cpp/iris26864/bridge'
for x in ('compile_26925_shaders.sh','compile_26925_hr_spirv.sh'):
 t=(R/x).read_text()
 assert 'spirv-opt --target-env=' in t and 'spirv-val --target-env ' in t
 assert '16.5.0' in t
 subprocess.run(['bash','-n',str(R/x)],check=True)
sh=(J/'GlesIris26870PostAmazeChroma.kt').read_text()
m=list(re.finditer(r'val shader\s*=\s*"""',sh));assert len(m)==1
body=textwrap.dedent(sh[m[0].end():].split('""".trimIndent()',1)[0]).strip()
assert body.startswith('#version 300 es') and body.count('void main()')==1
# Actual 26925 V1 failed job 131687883560 at real ESSL compilation:
# GLSL ES 300 reserves `coherent`; never accept GLSL reserved qualifiers as
# scalar/vector variable identifiers. This static gate runs BEFORE pinned
# glslang, which is still mandatory and is never replaced by this preflight.
reserved={"coherent", "restrict", "volatile", "readonly", "writeonly", "shared",
          "sample", "subroutine", "filter", "attribute", "varying", "uniform",
          "precision", "layout", "invariant", "centroid", "flat", "smooth",
          "patch", "buffer", "struct", "const", "in", "out", "inout"}
def reserved_declarations(source):
    # Ignore comments: the banned words may appear in explanatory prose.
    clean=re.sub(r'/\*.*?\*/', ' ', source, flags=re.S)
    clean=re.sub(r'//[^\n]*', '', clean)
    declarators=re.finditer(r'\b(?:float|int|uint|bool|vec[234]|ivec[234]|uvec[234]|bvec[234])\s+([A-Za-z_][A-Za-z0-9_]*)\b',clean)
    return [m.group(1) for m in declarators if m.group(1) in reserved]
assert not reserved_declarations(body), ('GLSL reserved identifier in 26925 inline shader',reserved_declarations(body))
assert 'float localCoherence=' in body and 'localCoherence*outlierConfidence' in body
# Negative regression: undo the specific correction and prove the gate rejects
# the previous Actions-shipped V1 typo, not merely a made-up unrelated token.
bad=body.replace('float localCoherence=', 'float coherent=',1)
assert reserved_declarations(bad)==['coherent'], reserved_declarations(bad)
for t in ('uIris26925SupportPresent','uIris26925OriginalFrames','uIris26925ShotByRgb','uIris26925ReadByRgb'):
 assert body.count('uniform') and body.count(t)==2 or body.count(t)>=2,t
assert body.count('uniform int uIris26922SrOn;')==1
assert 'uniform int uIris26923SrOn;' not in body
assert 'uIris26922ShotVariance;' not in body and 'uIris26922ReadVariance;' not in body
assert 'uniform int uIris26924BOff;' in body and 'uniform int uIris26924ClipPresent;' in body
assert (B/'Iris26925_raw_cfa_weight.comp').read_text().count('void main()')==1
assert (B/'Iris26925_support_finish.comp').read_text().count('void main()')==1
assert 'binding=6,r32f' in (B/'Iris26924_raw_adjoint.comp').read_text()
assert 'Iris26925_raw_cfa_weight' in (R/'compile_26925_hr_spirv.sh').read_text()
assert 'Iris26885WronskiChromaGuide' in (R/'compile_26925_hr_spirv.sh').read_text()
# The V1 runner swallowed compiler stdout inside a success-only receipt.
# Replay the *exact current* ERR trap against a deliberately failing compiler
# to prove GitHub logs expose the error and preserve the nonzero return code.
import tempfile
shell=(R/'compile_26925_shaders.sh').read_text()
assert 'set -eEuo pipefail' in shell and shell.count('exec 3>&1')==1
match=[line for line in shell.splitlines() if line.startswith("trap 'rc=$?") and line.endswith("' ERR")]
assert len(match)==1,('missing/duplicated actual V2 compiler diagnostics trap',match)
with tempfile.TemporaryDirectory(prefix='p26925_glsl_fail_visible_') as d:
    fixture=("set -eEuo pipefail\nOUT=\""+d+"\"\nexec 3>&1\n"+
             match[0]+"\n{ echo 'glslang REAL FAIL: reserved keyword coherent'; false; } >\"$OUT/26925_CURRENT_GLSL_SPIRV_REAL_COMPILER.txt\" 2>&1\n")
    out=subprocess.run(['bash','-'],input=fixture,text=True,capture_output=True)
    assert out.returncode==1,(out.returncode,out.stdout,out.stderr)
    assert 'glslang REAL FAIL: reserved keyword coherent' in out.stdout,(out.stdout,out.stderr)
    assert '26925 BLOCKED: pinned shader compiler failed (exit 1)' in out.stdout
print('PASS 26925 exact shader ABI, native per-CFA variance, actual original RAW GLSL and unchanged historical compiler gates; REAL glslang/NDK PENDING')
