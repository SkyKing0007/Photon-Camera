#!/usr/bin/env python3
"""NARROW V2 infrastructure correction of exact 26903 V1 17-stage runner.
Original 26902 successful runner and failed V1 Night B runtime unchanged.
Correct obsolete 26902 archived historical TAR SHA receipt's ABSOLUTE filename;
execute exact V1 source/staging gates in their ORIGINAL generated runner context.
"""
from pathlib import Path
import hashlib
import re
import sys

ROOT=Path(sys.argv[1] if len(sys.argv)==2 else '.').resolve()
P=ROOT/'build_26903_iris_rawr.sh'
SHA_V1='5d932336627107556a1df870802b2e32046467d599ab4648fb57b7f78dc117ad'
SHA02='348b2d617ed36b40744d15eeba762bb64c589e45327f60f18454d54cbc4c64dc'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert P.is_file() and H(P)==SHA_V1,'BLOCK: V2 requires ORIGINAL exactly generated 26903 V1 runner before making changes'
assert H(ROOT/'build_26902_iris_rawr.sh')==SHA02,'BLOCK: original 26902 successful runner changed'
s=P.read_text()
STAGES=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES

def once(old,new):
    global s
    assert s.count(old)==1,('BLOCK V2 anchor cardinality',s.count(old),old[:120])
    s=s.replace(old,new,1)

def section(name):
    a=s.index('\n'+name+'(){')+1
    b=s.index('\n}',a)+2
    return s[a:b]

def append(name,fragment):
    global s
    old=section(name)
    assert old.endswith('\n}') and fragment.strip()
    s=s.replace(old,old[:-2]+'\n'+fragment.strip('\n')+'\n}',1)

# Keep the historical V1 stage check fully executed with its own V1 source and
# EXACT archived/derived V1 script bytes. A V2 runner SHA cannot pass V1 root.
once(' python3 -S stage_26903_root.py\n sha256sum -c 26903_HANDOFF_HASHES.sha256',
     ' python3 -S validate_26903_v1_frozen_stage.py\n sha256sum -c 26903_HANDOFF_HASHES.sha256')
# Actual observed 26903 V1 failure: successful 26902 receipt has an ABSOLUTE
# old Actions workspace path. sha256sum -c dereferenced it after ZIP extract.
BAD=' (cd "$ARTDIR/build_26902_iris_rawr_outputs" && sha256sum -c 26901_historical_candidate_app_source.tar.gz.sha256 >/dev/null) || fail \'historical 26901 archive corrupted\''
GOOD=' python3 -S verify_26903_v2_archive_receipt.py "$T01" "$ARTDIR/build_26902_iris_rawr_outputs/26901_historical_candidate_app_source.tar.gz.sha256" || fail \'26901 original successful archive missing or SHA mismatch after archive relocation\''
once(BAD,GOOD)
# The new commit must be a child of the exact failed V1 commit (V1 root trigger
# immutable) and original SUCCESSFUL 26902; verify the CUMULATIVE git diff,
# not just the V2 repair ZIP delta.
once('diff -u 26903_REPOSITORY_UPLOAD_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort)',
     'diff -u 26903_V2_CUMULATIVE_REPOSITORY_ALLOWLIST.txt <(git diff --name-only "$REPO_SCAFFOLD_BASE_COMMIT"..HEAD | LC_ALL=C sort)')
once("git merge-base --is-ancestor \"$REPO_SCAFFOLD_BASE_COMMIT\" HEAD || fail '26903 successful 26902 parent not ancestor'",
     "git merge-base --is-ancestor \"$REPO_SCAFFOLD_BASE_COMMIT\" HEAD || fail '26903 successful 26902 parent not ancestor'\n git merge-base --is-ancestor '7619f129b14d8077811fb3b8b414bc97cdb6c449' HEAD || fail '26903 V2 requires exact failed V1 commit as ancestor, no silent source rollback'")
append('verify_package', '''
 # V2 revised single-trigger infrastructure seal; original V1 seal above remains intact.
 python3 -S stage_26903_v2_root.py --runner
 sha256sum -c 26903_V2_HANDOFF_HASHES.sha256 >/dev/null || fail '26903 V2 repair payload SHA drift'
 sha256sum -c 26903_V2_GENERATED_BUILD_SHA256.txt >/dev/null || fail '26903 V2 exact generated/EXECUTED runner mismatch'
 python3 -S test_26903_v2_archive_receipt.py
 python3 -S test_26903_v2_sealed_negatives.py
 [[ "$(sha TRIGGER_26903_V2.txt)" == "$(printf 'RUN_26903_B_NIGHT_ARCHIVED_RECEIPT_RELOCATION_V2\\n' | sha256sum | awk '{print $1}')" ]] || fail '26903 V2 immutable exact trigger changed'
''')
append('clean_extract_replay','''
 # Recheck actual downloaded original archived receipt after the full inherited
 # 17 stages; do NOT rebase or modify original successful 26902 receipt bytes.
 python3 -S verify_26903_v2_archive_receipt.py "$ARTDIR/build_26902_iris_rawr_outputs/26901_historical_candidate_app_source.tar.gz" "$ARTDIR/build_26902_iris_rawr_outputs/26901_historical_candidate_app_source.tar.gz.sha256" || fail '26901 historical original SHA drifted across assemble'
 python3 -S stage_26903_v2_root.py --runner
 python3 -S test_26903_v2_archive_receipt.py
 python3 -S test_26903_v2_sealed_negatives.py
''')
# Architectural invariant: the original 17 functions, all existing compiler,
# native, gradle, archive source and candidate patch commands remain unchanged.
assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',s) if x in STAGES)==STAGES
assert s.count('sha256sum -c 26901_historical_candidate_app_source.tar.gz.sha256')==0
assert s.count('verify_26903_v2_archive_receipt.py "$T01"')==1
assert s.count('python3 -S validate_26903_v1_frozen_stage.py')==1
assert len(re.findall(r'(?m)^\s*\./gradlew :app:assembleDebug --stacktrace',s))==1
assert '$ARTDIR/build_26901_iris_rawr_outputs/' not in s
assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in s
assert 'sha256sum -c "$ARTDIR/' not in s
P.write_text(s)
print('PASS 26903 V2 17 original stage order/real compilers unchanged; original V1 negative and real archive receipt relocation fixed, output SHA256',H(P))
