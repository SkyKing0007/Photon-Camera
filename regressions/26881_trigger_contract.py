#!/usr/bin/env python3
"""Permanent regression for real failed Actions run 40402359994.
Exact 26881 build generated runner, workflow and trigger are one contract.
Do not pass based only on the workflow's preflight grep; run the generated
Bash verify_package() function's condition before build's own entry.
"""
from pathlib import Path
import ast,re,sys
ROOT=Path(__file__).resolve().parents[1]
name='RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R5'
trigger=(ROOT/'TRIGGER_26881.txt').read_text()
workflow=(ROOT/'.github/workflows/build-26881-iris-rawr.yml').read_text()
generator=(ROOT/'generate_26881_build.py').read_text()
assert trigger==name+'\n', 'Stage 3 trigger drift'
assert workflow.count("grep -Fx '"+name+"' TRIGGER_26881.txt")==1,'Stage 2 marker missing'
assert re.search(r"s=s.replace\('RUN_26881_ORIGINAL_125_WRONSKI_WAVELET_HIGHLIGHT_V1','"+re.escape(name)+r"'\)",generator),'generator fails to migrate runner marker'
source=ast.parse(generator)
package=[x for x in source.body if isinstance(x,ast.FunctionDef) and x.name=='package']
assert len(package)==1,'missing/duplicated actual generator package stage'
module=ast.Module(body=package,type_ignores=[]);ast.fix_missing_locations(module)
ns={};exec(compile(module,str(ROOT/'generate_26881_build.py'),'exec'),ns)
# Reproduce the *real* bad R3 case: the source form inherited from 26880
# after global version rename still contained this marker. R3 left R1 there.
old="grep -Fx 'RUN_26881_ORIGINAL_125_WRONSKI_WAVELET_HIGHLIGHT_V1' TRIGGER_26881.txt >/dev/null || fail 'wrong 26881 trigger'"
fixed=ns['package'](old)
assert fixed.count("grep -Fx '"+name+"' TRIGGER_26881.txt")==1,'exact prior trigger transformation failed'
assert "RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R1" not in fixed
assert "RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R3" not in fixed
# This is intentional negative test: stage3 R4 against runner R1/R3 MUST fail.
def verify(text):
 checks=re.findall(r"(?m)^\s*grep -Fx '([^']+)' TRIGGER_26881\.txt\b",text)
 return checks==[name]
assert verify(fixed)
assert not verify(fixed.replace(name,'RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R1'))
assert not verify(fixed.replace(name,'RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R3'))
if len(sys.argv)>1:
 runner=Path(sys.argv[1]).resolve().read_text()
 body=re.findall(r'(?ms)^verify_package\(\)\{(.*?)^\}',runner)
 assert len(body)==1,'actual generated runner verify_package function missing/duplicate'
 assert verify(body[0]),'actual generated verify_package rejects uploaded Stage 3 marker'
 # Unchanged package stage may mention prior trigger as a comment, but no
 # executable grep may accept it. Guard against two possible marker checks.
 assert sum('TRIGGER_26881.txt' in line and 'grep -Fx' in line for line in body[0].splitlines())==1
 print('PASS actual generated runner/workflow/trigger all agree on R4 marker')
else:
 print('PASS R3 trigger failure reproduced and repaired against actual generator package()')
