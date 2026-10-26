#!/usr/bin/env python3
"""Permanent regression for real GitHub failure 40410435003 (R5).
Run the actual generated verify_package trigger shell command, including the
inherited `test -f ... && grep -Fx ... || fail` prefix. A synthetic
bare-grep fixture incorrectly passed previous pre-handoff checks.
"""
from pathlib import Path
import ast,re,sys,tempfile,subprocess
ROOT=Path(__file__).resolve().parents[1]
MARKER='RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R6'
TRIGGER='TRIGGER_26881.txt'
assert (ROOT/TRIGGER).read_bytes()==(MARKER+'\n').encode(), 'Stage 3 trigger bytes drift'
workflow=(ROOT/'.github/workflows/build-26881-iris-rawr.yml').read_text()
assert workflow.count("grep -Fx '"+MARKER+"' TRIGGER_26881.txt")==1,'workflow marker drift'
generator=(ROOT/'generate_26881_build.py').read_text()
old_marker='RUN_26881_ORIGINAL_125_WRONSKI_WAVELET_HIGHLIGHT_V1'
assert generator.count("s=s.replace('"+old_marker+"','"+MARKER+"')")==1,'generator marker migration absent'
# Extract actual generator package() function, not an imitation.
node=ast.parse(generator)
found=[n for n in node.body if isinstance(n,ast.FunctionDef) and n.name=='package']
assert len(found)==1
mod=ast.Module(body=found,type_ignores=[]);ast.fix_missing_locations(mod)
ns={};exec(compile(mod,str(ROOT/'generate_26881_build.py'),'exec'),ns)
# Recreate the exact original inherited successful stage's combined command.
original=" test -f TRIGGER_26881.txt && grep -Fx '"+old_marker+"' TRIGGER_26881.txt >/dev/null || fail 'wrong 26881 trigger'"
assert '&& grep -Fx' in original
converted=ns['package'](original)
assert ("&& grep -Fx '"+MARKER+"' TRIGGER_26881.txt") in converted
assert old_marker not in converted

def extract_shell_condition(stage_body):
 # Comments and fixture text are not executable trigger checks.
 lines=[line.strip() for line in stage_body.splitlines() if 'TRIGGER_26881.txt' in line and 'grep -Fx' in line and not line.lstrip().startswith('#')]
 assert len(lines)==1,('expected exactly one executable Stage 3 gate',lines)
 line=lines[0]
 assert re.search(r"\btest -f TRIGGER_26881\.txt\s*&&\s*grep -Fx '"+re.escape(MARKER)+r"' TRIGGER_26881\.txt",line),('wrong combined trigger command',line)
 assert re.search(r"\|\|\s*fail\s+['\"]wrong 26881 trigger['\"]",line),('trigger failure not fail-closed',line)
 return line

def execute(line,content):
 with tempfile.TemporaryDirectory(prefix='photon_26881_real_trigger_') as td:
  if content is not None:(Path(td)/TRIGGER).write_bytes(content.encode())
  script='set -euo pipefail\nfail(){ echo "EXPECTED-GATE-FAIL: $*" >&2; exit 79; }\n'+line+'\n'
  return subprocess.run(['bash','-c',script],cwd=td,text=True,capture_output=True)

fixture=extract_shell_condition(converted)
assert execute(fixture,MARKER+'\n').returncode==0,'fixed exact inherited shell condition rejects correct R6'
assert execute(fixture,'RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R5\n').returncode!=0,'old marker accepted'
assert execute(fixture,None).returncode!=0,'missing Stage 3 trigger accepted'
assert execute(fixture,MARKER+'\nEXTRA\n').returncode==0,'grep -Fx inherited semantics drift'
if len(sys.argv)>1:
 runner=Path(sys.argv[1]).resolve().read_text()
 body=re.findall(r'(?ms)^verify_package\(\)\{(.*?)^\}',runner)
 assert len(body)==1,'actual generated verify_package missing or duplicated'
 line=extract_shell_condition(body[0]);assert execute(line,MARKER+'\n').returncode==0,'actual generated script rejects R6'
 assert execute(line,'RUN_26881_SPEKTRA112_FOV_CHROMA_HIGHLIGHT_R5\n').returncode!=0,'actual runner wrongly accepts R5'
 assert execute(line,None).returncode!=0,'actual runner accepts missing marker'
 print('PASS R6 real generated verify_package shell trigger + workflow + file, R5/missing negatives')
else:
 print('PASS exact inherited combined trigger shell condition, old R5 and missing negative cases')
