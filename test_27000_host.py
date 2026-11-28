import pathlib,subprocess,tempfile,sys
R=pathlib.Path(__file__).resolve().parent
def run(*a):subprocess.run(list(map(str,a)),cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='27000-host-') as d:
 t=pathlib.Path(d)
 run('javac','-d',t,R/'Parse27000Java.java')
 run('java','-cp',t,'Parse27000Java',*[R/p for p in (R/'27000_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines() if p.endswith('.java')])
 run(sys.executable,'-S',R/'test_27000_math.py')
