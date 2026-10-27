#!/usr/bin/env python3
"""Historical 26881 Actions failures: test inherited combined trigger, identity,
compiler stage and 26880/26881 source ownership in the ACTUAL successor generator.
Supplement only: the real previous runner is SHA-checked in Actions before use.
"""
from pathlib import Path
import ast,re,tempfile,subprocess,hashlib
R=Path(__file__).resolve().parents[1]
s=(R/'generate_26882_build.py').read_text();tree=ast.parse(s)
assert "PARENT='8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5'" in s
assert "prior.replace('26881','26882')" in s
edits=re.findall(r"edit\('([a-z_]+)',",s)
assert len(set(edits))==len(edits)
assert not (set(edits)&{'compile_languages','compile_native','assemble','install_frozen_candidate_live','postbuild_proof','prepare_glslang','verify_native_glslang_handoff'}),'inherited compiler/freeze/assemble stage modified'
assert 'RUNTIME_ARTIFACT_ID="12695143651"' in s
assert 'RUNTIME_ARTIFACT_SHA="b83eb47da7da71fc75a82aa1bb562acb6169379e65ee483f60ee92702cb790da"' in s
assert 'RUNTIME_TAR_SHA="5cd951c92e7782bf12812cb5f6e9adb76aabd7255515512e5196e7688f2a3e87"' in s
assert 'MECHANICS_GIT_BLOB="2a503622fd337a7355385fbf82706c4b089de777"' in s
assert 'runtime_changed_files=3' in s and 'protected_source=2006' in s
assert "sha256sum -c \"$ROOT/26881_BASE_26880_FULL_APP.sha256\"" in s
assert 'cp -a "$BASE" "$H80"' in s
assert 'verify_26880_spektra_abi.py "$H80/app"' in s
assert 'regressions/26881_spektra_chroma_clip.py "$H80" "$BASE"' in s
assert 'verify_26881_expanded_glsl.py "$BASE"' in s
assert 'verify_26882_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in s
# Get the exact function source, not an imitation grep-line fixture.
fn=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='package']
assert len(fn)==1
module=ast.Module(body=fn,type_ignores=[]);ast.fix_missing_locations(module)
ns={};exec(compile(module,str(R/'generate_26882_build.py'),'exec'),ns)
old='RUN_26882_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R6';new='RUN_26882_SPEKTRA_ROTATED_RAW_B_WHITE_OFF_V1'
source="verify_package(){\n test -f TRIGGER_26882.txt && grep -Fx '"+old+"' TRIGGER_26882.txt >/dev/null || fail 'wrong 26882 trigger'\n}"
converted=ns['package'](source)
assert old not in converted and new in converted
matches=[x.strip() for x in converted.splitlines() if 'TRIGGER_26882.txt' in x and 'grep -Fx' in x]
assert len(matches)==1 and matches[0].startswith('test -f TRIGGER_26882.txt && grep -Fx')
def call(data):
 with tempfile.TemporaryDirectory(prefix='26882_real_trigger_') as td:
  if data is not None:(Path(td)/'TRIGGER_26882.txt').write_text(data)
  sh='set -euo pipefail\nfail(){ exit 79; }\n'+matches[0]+'\n'
  return subprocess.run(['bash','-c',sh],cwd=td,capture_output=True).returncode
assert call(new+'\n')==0
assert call(old+'\n')!=0
assert call(None)!=0
assert call(new+'\nEXTRA\n')==0,'inherited grep -Fx semantics changed'
# Prove workflow actually uses new marker, and does not react to old 26881 trigger.
w=(R/'.github/workflows/build-26882-iris-rawr.yml').read_text()
assert "      - 'TRIGGER_26882.txt'" in w
assert "      - 'TRIGGER_26881.txt'" not in w
assert w.count('bash build_26882_iris_rawr.sh')==1
assert 'bash build_26881_iris_rawr.sh' not in w
assert "test \"$(sha256sum build_26881_iris_rawr.sh | awk '{print $1}')\" = '8e9d44d66e4c955c105d136a1c380206ae93b671b9e57806412c2c991a791fc5'" in w
assert 'sha256sum -c 26882_GENERATED_BUILD_SHA256.txt' in w
assert 'bash -n build_26882_iris_rawr.sh' in w
print('PASS 26882 actual generator AST, inherited compiler stage freeze, real combined trigger shell valid/wrong/missing, sha-pinned successful 26881 script and artifact identity, 26880/26881 source domain routing')
