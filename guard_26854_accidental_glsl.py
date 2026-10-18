#!/usr/bin/env python3
# 26854 bounded Actions checkout repair: identical-to-original 50 generated GLSL only.
# THIS NEVER CHANGES THE GITHUB BRANCH. All actions are within ephemeral checkout.
from pathlib import Path
import hashlib,subprocess,shutil,sys
ROOT=Path.cwd()
MANIFEST=ROOT/'26854_ACCIDENTAL_GLSL_EXACT_SHA256.txt'
def git(*args): return subprocess.check_output(['git',*args],text=True).splitlines()
expected={}
for line in MANIFEST.read_text().splitlines():
 sha,rel=line.split('  ',1)
 assert len(sha)==64 and rel.startswith('glsl_static/') and rel not in expected,(sha,rel)
 expected[rel]=sha
assert len(expected)==50,len(expected)
tracked=git('ls-files','--','glsl_static')
assert tracked==sorted(expected),(len(tracked),sorted(set(tracked)^set(expected)))
for rel,sha in expected.items():
 p=ROOT/rel
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sha,('inherited unexpected shader bytes',rel)
 assert git('show',f'HEAD:{rel}') ,('not in HEAD',rel)
# All content is verified against EXACT original accidental uploaded bytes.
subprocess.run(['git','rm','-r','-q','--cached','--','glsl_static'],check=True)
shutil.rmtree(ROOT/'glsl_static')
assert not git('ls-files','--','glsl_static')
assert git('diff','--cached','--name-only','--diff-filter=D','--','glsl_static')==sorted(expected)
assert not (ROOT/'glsl_static').exists()
print('PASS 26854 exactly 50 original-accidental generated GLSL bytes attested; temporary Actions checkout index cleaned; GitHub HEAD unchanged')
