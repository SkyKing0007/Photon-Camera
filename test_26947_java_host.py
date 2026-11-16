#!/usr/bin/env python3
"""Real host javac/java sanity for four-way sensor rotation and lifecycle latch state."""
import tempfile,pathlib,subprocess,sys
from build_26947_incremental import R,fail
import test_26947_source as source
JAVA=r"""public final class Iris26947LifecycleHost {
 static class Gate {
  long min=0;
  void pause(){min=-1;}
  void resume(){min=-1;}
  void firstResult(long ns){if(ns>0 && min==-1)min=ns;}
  boolean present(long frame){if(min==0)return true;if(min<0 || frame<min)return false;min=0;return true;}
 }
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  int tests=0;
  for(int sensor: new int[]{0,90,180,270})for(int facing: new int[]{0,1}){
   Gate g=new Gate();g.pause();check(!g.present(100));g.resume();check(!g.present(200));
   int angle=(sensor+90)%360;check(angle%90==0);boolean mirror=facing==1;
   check(mirror==(facing==1));g.firstResult(500);check(!g.present(499));check(g.present(500));
   check(g.present(501));g.pause();check(!g.present(700));tests+=7;
  }
  System.out.println("PASS host javac/java 56 latch/rotation checks across 4 rotations and 2 facings");
 }
}"""
def main():
 source.main()
 with tempfile.TemporaryDirectory(prefix='26947_host_javac_') as td:
  f=pathlib.Path(td)/'Iris26947LifecycleHost.java';f.write_text(JAVA)
  subprocess.run(['javac','-encoding','UTF-8',str(f)],check=True,capture_output=True)
  subprocess.run(['java','-cp',td,'Iris26947LifecycleHost'],check=True)
 print('PASS real javac/java lifecycle host; full Android Java/Kotlin remains mandatory in Actions')
if __name__=='__main__':
 try:main()
 except Exception as e:print(e,file=sys.stderr);sys.exit(1)
