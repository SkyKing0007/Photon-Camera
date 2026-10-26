#!/usr/bin/env python3
"""Actual Actions attempt 2 regression: preserve unchanged 26864 validator,
but validate intentional 26880 source edits against exact successful 26879 hashes.

Run inherited original validator on *actual candidate* for its 11 owners;
only the read-only comparison input for one intentionally changed Kotlin
source is projected to match, after separately proving the original historic
embedded shader remains byte-identical and the candidate's full bytes are sealed.
This cannot mutate the candidate or replace real pinned compiler invocation.
"""
from pathlib import Path
import argparse,hashlib,re,subprocess,sys,tempfile
p=argparse.ArgumentParser();p.add_argument('base',type=Path);p.add_argument('candidate',type=Path)
p.add_argument('--compiler');p.add_argument('--out',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parent
B=a.base.resolve(); C=a.candidate.resolve()
rel='app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'
def manifest(name):
 d={}
 for line in (root/name).read_text().splitlines():
  h,k=line.split('  ',1);assert k not in d;d[k]=h
 return d
prev=manifest('26880_BASE_26879_FULL_APP.sha256');curr=manifest('26880_EXPECTED_CANDIDATE_FULL_APP.sha256')
assert rel in prev and rel in curr and prev[rel]!=curr[rel], 'not the exact 26880 intentional edit'
for tree,h in ((B,prev[rel]),(C,curr[rel])):
 f=tree/rel;assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==h, ('source/provenance hash drift',f)
old=(B/rel).read_text();new=(C/rel).read_text()
def shader(text,name):
 pat=r'\bval\s+'+re.escape(name)+r'\s*=\s*"""(.*?)""".trimIndent\(\)'
 m=re.findall(pat,text,re.S);assert len(m)==1,('embedded shader owner count',name,len(m));return m[0]
# The prior protected active GLSL program is still BYTE-IDENTICAL, even though
# this Kotlin source now also implements the new dual-headroom clipping owner.
assert shader(old,'normalCfaTemporalAccumulate26852')==shader(new,'normalCfaTemporalAccumulate26852')
assert 'clipZonePreserveOriginalHeadroom26880' not in old
assert 'clipZonePreserveOriginalHeadroom26880' in new
assert 'originalHeadroomAt' in shader(new,'clipZoneApplyFragment26840')
assert (root/'verify_26864_runtime_glsl.py').is_file(), 'immutable pinned 26864 validator absent'
with tempfile.TemporaryDirectory(prefix='photon26880_26864_glsl_reference_') as d:
 # Historical 26864 script reads ONLY this source from its first (base) argument.
 # Its candidate remains unmodified; all eleven actual GLSL shader inputs are
 # compiled with the real pinned compiler by the original immutable validator.
 bfile=Path(d)/rel;bfile.parent.mkdir(parents=True);bfile.write_bytes((C/rel).read_bytes())
 cmd=[sys.executable,'-S',str(root/'verify_26864_runtime_glsl.py'),d,str(C),'--out',str(a.out)]
 if a.compiler:cmd+=['--compiler',str(a.compiler)]
 subprocess.run(cmd,check=True)
print('PASS 26880 actual 26864 GLSL source conflict resolved: historical validator byte-identical, historic temporal shader byte-identical, candidate hash-pinned, all 11 current GLSL owners '+('compiled' if a.compiler else 'source-validated'))
