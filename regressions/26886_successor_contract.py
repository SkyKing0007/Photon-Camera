#!/usr/bin/env python3
"""26886 actual staged source, historical compiler continuity and unique Actions trigger."""
from pathlib import Path
import hashlib,re
R=Path(__file__).resolve().parent.parent
workflow=(R/'.github/workflows/build-26886-iris-rawr.yml').read_text()
old_gen='generate_26885_build.py';new_gen='generate_26886_build.py';gen=(R/new_gen).read_text()
assert workflow.count("      - 'TRIGGER_26886.txt'")==1
assert "      - 'TRIGGER_26885.txt'" not in workflow.split('  workflow_dispatch:')[0]
assert workflow.count('bash build_26886_iris_rawr.sh')==1
assert 'bash build_26885_iris_rawr.sh' not in workflow
assert workflow.count('sha256sum -c 26886_GENERATED_BUILD_SHA256.txt')==1
assert 'sha256sum -c 26885_GENERATED_BUILD_SHA256.txt' in workflow
assert 'sha256sum -c 26884_GENERATED_BUILD_SHA256.txt' in workflow
assert '2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379' in workflow
assert 'python3 -S stage_26885_root.py' in workflow
assert 'python3 -S stage_26886_root.py' in workflow
assert workflow.index('python3 -S generate_26885_build.py .')<workflow.index('python3 -S generate_26886_build.py .')
assert "test -f TRIGGER_26886.txt && grep -Fx 'RUN_26886_B_ON_WRONSKI_CHROMA_NOISE_ALIAS_V1'" in workflow
assert 'IrisCamera-0.9726886-26886-iris-rawr-debug.apk' in workflow
assert 'build_26886_iris_rawr_outputs/' in workflow
assert 'photon-26886-b-on-rawr-chroma-denoise-false-color' in workflow
assert 'if-no-files-found: error' in workflow
assert "sha256sum -c 26886_HANDOFF_HASHES.sha256" in workflow
assert 'bash -n build_26886_iris_rawr.sh' in workflow
assert all(x in gen for x in ('17-stage','sha256','make_candidate','compile_modified_runtime_shaders','clean_extract_replay','2138db01cbfb3a8421c12e54ba29d4f0a893d1cdd4a219ee34a40a4dc0c54379','26885_actions_40604341240_historical_scope.py'))
assert 'regressions/26886_historical_scope_all_stages.py' in gen
# Permanent exact Actions 40621816379 generator-mechanics failure regression.
# The 26885 V2 prior stage has TWO references to the original 26884 runner.
# Its proven generator used complete replace; no ambiguity-prone once assertion.
mechanics=gen[gen.index('def mechanics(s):'):gen.index("edit('verify_successful_mechanics',mechanics)")]
assert "s.count(anchors[0][0])==2" in mechanics
assert "s=s.replace(before,after)" in mechanics
assert "return once(once(once" not in mechanics
assert "build_26884_iris_rawr.sh" in mechanics and "build_26885_iris_rawr.sh" in mechanics
# Permanent second defect: the 26885 historical regression was already
# restored to its original name before source-domain rewriting.
assert "if '26886_actions_40604341240_historical_scope.py' in line" not in gen
assert "if 'python3 -S regressions/26885_actions_40604341240_historical_scope.py' in line" in gen
assert "len(matches)==1" in gen
assert "26884 historical-domain leak" in gen and "26885 chroma regression rebound to 26886" in gen
assert 'verify_26880_rawr_shader_universe.py' in gen
assert 'real compiler' in gen.lower()
for x in ('run: |','branches: [experimental-clean-photon-rebuild]','permissions:','actions: read','contents: read','uses: actions/checkout@v5','uses: actions/setup-java@v5','uses: actions/setup-python@v5'):
 assert x in workflow
assert workflow.count('actions/upload-artifact@v4')==1
assert all((R/x).is_file() for x in (new_gen,'stage_26886_root.py','regressions/26886_historical_scope_all_stages.py'))
assert not any(x in workflow for x in ('pull_request:', 'schedule:', 'build_26885_iris_rawr_outputs/'))
print('PASS 26886 exact unique workflow trigger, successful 26885 V2 17-stage chain inherited, strict current and historical compiler source guards')
