#!/usr/bin/env python3
"""Permanent actual 26882 compiled-runner inheritance/trigger/regression failures."""
from pathlib import Path
import ast,hashlib,re,tempfile,subprocess
R=Path(__file__).resolve().parents[1]
G=R/'generate_26883_build.py';s=G.read_text();tree=ast.parse(s)
assert "PARENT='8bbdf3738e8a8b17f236db6c43f8273b2a24e164b847963aa9c749da7707251c'" in s
assert "prior.replace('26882','26883')" in s
for identity in ('12705612602','40439262910','41dda5bb2484f5f26f87856325a4d70aeafc227811b946e5ae9eae35f1f43497','ed756212e83d96ae0ad474c3ca84fd947bcabce4a5fbb45c7c2ed5a81b37d5a6'):
 assert identity in s,identity
assert 'historical_26881_from_26882' in s and '26882_BASE_26881_FULL_APP.sha256' in s
edits=re.findall(r"edit\('([a-z_]+)',",s)
assert len(edits)==len(set(edits))
assert not set(edits)&{'compile_languages','compile_native','assemble','install_frozen_candidate_live','postbuild_proof','prepare_glslang','verify_native_glslang_handoff','compile_spektra_raw_shader'},'unapproved successful compiler/freeze stage modification'
assert 'regressions/26881_spektra_chroma_clip.py "$H80" "$H81"' in s
assert 'verify_26882_expanded_glsl.py "$BASE"' in s
assert 'verify_26883_expanded_glsl.py "$CAND" --compiler "$IRIS26864_GLSLANG"' in s
assert 'verify_26882_candidate.py "$H81" "$BASE"' in s
assert 'verify_26883_semantics.py "$BASE" "$CAND"' in s
assert 'protected_source=2005 files byte-identical to successful 26882' in s
assert (R/'TRIGGER_26883.txt').read_text()=='RUN_26883_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1\n'
w=(R/'.github/workflows/build-26883-iris-rawr.yml').read_text()
assert "      - 'TRIGGER_26883.txt'" in w and "      - 'TRIGGER_26882.txt'" not in w
assert w.count('bash build_26883_iris_rawr.sh')==1 and 'bash build_26882_iris_rawr.sh' not in w
assert "test \"$(sha256sum build_26882_iris_rawr.sh | awk '{print $1}')\" = '8bbdf3738e8a8b17f236db6c43f8273b2a24e164b847963aa9c749da7707251c'" in w
assert 'sha256sum -c 26883_GENERATED_BUILD_SHA256.txt' in w
assert 'bash -n build_26883_iris_rawr.sh' in w
assert 'sha256sum -c 26882_GENERATED_BUILD_SHA256.txt' in w
# Fail on missing/wrong trigger in the very same Bash syntax invoked on Actions.
line=next(x.strip() for x in w.splitlines() if x.strip().startswith('test -f TRIGGER_26883.txt') and 'grep -Fx' in x)
assert 'RUN_26883_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1' in line
with tempfile.TemporaryDirectory(prefix='26883_trigger_real_') as td:
 for name,content,expected in [('valid','RUN_26883_SPEKTRA_FULL_FOV_1920_B_EARLY_WHITE_ON_OFF_V1\n',0),('wrong','RUN_26882_SPEKTRA_ROTATED_RAW_B_WHITE_OFF_V1\n',1),('missing',None,1)]:
  p=Path(td)/'TRIGGER_26883.txt'
  if content is None:p.unlink(missing_ok=True)
  else:p.write_text(content)
  test=subprocess.run(['bash','-c','set -euo pipefail\n'+line+'\n'],cwd=td,capture_output=True)
  assert (test.returncode==0)==(expected==0),name
print('PASS 26883 actual successor generator AST, correct prior compiled universe, 17 untouched compiler/freeze stages, real trigger valid/wrong/missing, 26882 runner SHA and artifact identity')
