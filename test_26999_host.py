#!/usr/bin/env python3
import pathlib,subprocess,tempfile,sys
R=pathlib.Path(__file__).resolve().parent;J=R/'app/src/main/java/com/particlesdevs/photoncamera'
def run(*a):subprocess.run(list(map(str,a)),cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='26999-host-') as d:
 t=pathlib.Path(d)
 run('javac','-d',t,R/'Test26999Xml.java',J/'settings/Iris26999XmlConfig.java',R/'Parse26999Java.java')
 run('java','-ea','-cp',t,'Test26999Xml')
 run('java','-cp',t,'Parse26999Java',*[R/p for p in (R/'26999_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines() if p.endswith('.java')])
 run(sys.executable,'-S',R/'test_26999_storage_host.py')
